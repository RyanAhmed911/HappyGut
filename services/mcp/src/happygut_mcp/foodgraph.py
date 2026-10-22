"""happygut-foodgraph: read-only MCP server over the HappyGut food knowledge graph.

Tools
- search_dish:          English / Bangla / Banglish name (or a sentence) → candidate dishes
- get_components:       a dish's gut-relevant components, ingredients, alternatives and sources
- explain_verdict_path: dish → component → Rule Card → cited source paths that apply to a profile

The server never computes verdicts (the engine does) and has no write tools. It holds no
patient data.

Run
    happygut-foodgraph                       # stdio (Claude Code / Claude Desktop)
    happygut-foodgraph --http --port 8100    # Streamable HTTP, requires MCP_BEARER_TOKEN

Environment
    HAPPYGUT_GRAPH_BACKEND   memory (default; built from approved seeds) | neo4j
    HAPPYGUT_INCLUDE_DRAFTS  1 to include draft seeds (development only; results are marked draft)
    NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD   for the neo4j backend
    MCP_BEARER_TOKEN         required for --http
"""

from __future__ import annotations

import argparse
import hmac
import os
from typing import Literal, Protocol

from pydantic import BaseModel, Field

from happygut_engine import Profile
from happygut_pipelines.graph import MemoryGraph, VerdictPathStep, profile_from
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
Phenotype = Literal["stricturing", "lactose_intolerant", "ibs_like_symptoms"]


class GraphBackend(Protocol):
    def search_dish(self, query: str, limit: int = 5): ...
    def get_components(self, dish_id: str) -> dict: ...
    def explain_verdict_path(self, dish_id: str, profile: Profile) -> list[VerdictPathStep]: ...


# ---------------------------------------------------------------- output models

class DishCandidate(BaseModel):
    dish_id: str
    name_en: str
    name_bn: str
    matched_name: str
    score: float = Field(description="Name match score 0-1 (trigram similarity)")


class DishSearchResult(BaseModel):
    query: str
    candidates: list[DishCandidate]
    note: str = ""


class DishComponents(BaseModel):
    dish_id: str
    name_en: str
    name_bn: str
    status: str
    level_basis: str
    components: dict[str, str] = Field(description="component → none | low | medium | high | unknown")
    ingredients: list[str]
    gentler_alternatives: list[str]
    sources: list[dict]


class SourceOut(BaseModel):
    key: str
    citation: str
    doi: str = ""
    pmid: str = ""
    licence: str = ""
    quote: str = ""


class PathStep(BaseModel):
    component: str
    level: str
    rule_id: str
    rule_title_en: str
    rule_title_bn: str
    recommendation_en: str
    recommendation_bn: str
    severity: int
    hard: bool
    evidence_level: str
    rule_status: str
    sources: list[SourceOut]


class VerdictPath(BaseModel):
    dish_id: str
    profile: dict
    steps: list[PathStep]
    note: str = "Evidence paths only. The verdict itself is computed by the HappyGut engine, not by this server."


# ---------------------------------------------------------------- server

def build_server(graph: GraphBackend) -> MCPServer:
    server = MCPServer(
        name="happygut-foodgraph",
        title="HappyGut food knowledge graph",
        instructions=(
            "Read-only access to HappyGut's food knowledge graph for IBD: Bangladeshi dishes, their "
            "gut-relevant components, and cited dietary Rule Cards. Never presents a food as 'safe'; "
            "verdicts come from the HappyGut engine. Contains no patient data."
        ),
        version="0.1.0",
    )

    @server.tool(annotations=READ_ONLY)
    def search_dish(
        query: str = Field(min_length=1, max_length=200, description="Dish name or a sentence, in English, Bangla or Banglish"),
        limit: int = Field(default=5, ge=1, le=20),
    ) -> DishSearchResult:
        """Find dishes by name. Handles misspellings, Bangla script and names inside a sentence."""
        matches = graph.search_dish(query, limit=limit)
        return DishSearchResult(
            query=query,
            candidates=[DishCandidate(**m.__dict__) for m in matches],
            note="" if matches else "No dish matched; the meal check returns 'Not sure' and logs a knowledge gap.",
        )

    @server.tool(annotations=READ_ONLY)
    def get_components(dish_id: str = Field(pattern=r"^dish\.[a-z0-9_]+$")) -> DishComponents:
        """A dish's gut-relevant component levels, ingredients, gentler alternatives and sources."""
        try:
            return DishComponents(**graph.get_components(dish_id))
        except KeyError:
            raise ToolError(f"unknown dish {dish_id}") from None

    @server.tool(annotations=READ_ONLY)
    def explain_verdict_path(
        dish_id: str = Field(pattern=r"^dish\.[a-z0-9_]+$"),
        diagnosis: Literal["CD", "UC"] = Field(description="CD = Crohn's disease, UC = ulcerative colitis"),
        state: Literal["remission", "flare"] = "remission",
        phenotypes: list[Phenotype] = Field(default_factory=list),
    ) -> VerdictPath:
        """Dish → component → Rule Card → source paths that apply to this profile, hard safety rules first."""
        profile = profile_from(diagnosis, state, phenotypes)
        try:
            steps = graph.explain_verdict_path(dish_id, profile)
        except KeyError:
            raise ToolError(f"unknown dish {dish_id}") from None
        return VerdictPath(
            dish_id=dish_id,
            profile={"diagnosis": diagnosis, "state": state, "phenotypes": sorted(phenotypes)},
            steps=[
                PathStep(
                    component=s.component, level=s.level, rule_id=s.rule.id,
                    rule_title_en=s.rule.title_en, rule_title_bn=s.rule.title_bn,
                    recommendation_en=s.rule.recommendation_en, recommendation_bn=s.rule.recommendation_bn,
                    severity=s.rule.severity, hard=s.rule.hard, evidence_level=s.rule.evidence_level,
                    rule_status=s.rule.status,
                    sources=[SourceOut(**src.__dict__) for src in s.rule.sources],
                )
                for s in steps
            ],
        )

    return server


def graph_from_env() -> GraphBackend:
    include_drafts = os.environ.get("HAPPYGUT_INCLUDE_DRAFTS") == "1"
    if os.environ.get("HAPPYGUT_GRAPH_BACKEND", "memory") == "neo4j":
        from .neo4j_graph import Neo4jGraph

        return Neo4jGraph.from_env(include_drafts=include_drafts)
    return MemoryGraph.from_seeds(include_drafts=include_drafts)


# ---------------------------------------------------------------- HTTP with bearer token

class BearerAuth:
    """ASGI middleware: every HTTP request must carry `Authorization: Bearer <token>`."""

    def __init__(self, app, token: str):
        if not token or len(token) < 24:
            raise ValueError("MCP_BEARER_TOKEN must be set to a long random string")
        self.app, self.expected = app, f"Bearer {token}".encode()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            supplied = dict(scope.get("headers") or []).get(b"authorization", b"")
            if not hmac.compare_digest(supplied, self.expected):
                await send({"type": "http.response.start", "status": 401,
                            "headers": [(b"content-type", b"text/plain"), (b"www-authenticate", b"Bearer")]})
                await send({"type": "http.response.body", "body": b"unauthorized"})
                return
        await self.app(scope, receive, send)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--http", action="store_true", help="serve Streamable HTTP instead of stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8100)
    args = parser.parse_args()

    server = build_server(graph_from_env())
    if not args.http:
        server.run("stdio")
        return
    import uvicorn

    app = BearerAuth(server.streamable_http_app(), os.environ.get("MCP_BEARER_TOKEN", ""))
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
