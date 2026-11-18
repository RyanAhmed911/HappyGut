"""happygut-guidelines: read-only MCP server over HappyGut's cited Rule Cards.

Every Rule Card turns a sentence from published IBD dietary guidance into a structured rule:
which food component, from which level, for which diagnosis, disease state and condition, and how
strongly. Each card keeps the paper (DOI / PMID) and the exact sentence it relies on, reviewed by an
LLM judge (not by clinicians).

Tools
- search_rules:  keyword search, filtered by component, diagnosis, state or condition
- get_rule:      one Rule Card with its sources and exact quotes
- list_sources:  every cited paper and how many rules rely on it

Search is keyword-based over the approved cards; it never paraphrases a source. No patient data.

Run
    happygut-guidelines                       # stdio
    happygut-guidelines --http --port 8101    # Streamable HTTP, requires MCP_BEARER_TOKEN
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from happygut_pipelines.seeds import DEFAULT_SEEDS, _read
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from .common import READ_ONLY, run

Diagnosis = Literal["CD", "UC"]
State = Literal["remission", "flare"]
Phenotype = Literal["stricturing", "lactose_intolerant", "ibs_like_symptoms"]


class Source(BaseModel):
    key: str
    citation: str
    doi: str = ""
    pmid: str = ""
    licence: str = ""
    quote: str = Field(default="", description="Exact sentence retrieved from the source; empty = identity confirmed only")


class Rule(BaseModel):
    id: str
    title_en: str
    title_bn: str
    component: str
    min_level: str
    diagnoses: list[str]
    phenotypes: list[str] = Field(description="'any' or the conditions the rule is limited to")
    states: list[str]
    severity: int = Field(description="0 none · 1 mild · 2 moderate · 3 strong")
    hard: bool = Field(description="Hard safety rule, applied before any AI output")
    evidence_level: str
    recommendation_en: str
    recommendation_bn: str
    sources: list[Source]
    review: str = Field(description="How the card was reviewed")


class RuleSearch(BaseModel):
    query: str
    rules: list[Rule]
    note: str = "Rules are inputs to the HappyGut verdict engine. They never label a food 'safe' and are not personal medical advice."


class SourceSummary(BaseModel):
    key: str
    citation: str
    doi: str = ""
    pmid: str = ""
    licence: str = ""
    rules: list[str]
    has_quote: bool


class SourceList(BaseModel):
    sources: list[SourceSummary]


def load_rules(seeds: Path = DEFAULT_SEEDS, include_drafts: bool = False) -> list[Rule]:
    out = []
    for path in sorted((seeds / "rule_cards").glob("*.yaml")):
        raw = _read(path)
        if raw.get("status") != "approved" and not include_drafts:
            continue
        a = raw.get("applies_to", {})
        review = raw.get("review") or {}
        out.append(Rule(
            id=raw["id"], title_en=raw.get("title_en", ""), title_bn=raw.get("title_bn", ""), component=raw["component"],
            min_level=raw["min_level"], diagnoses=a.get("diagnosis", []), phenotypes=a.get("phenotype", ["any"]),
            states=a.get("state", []), severity=int(raw["severity"]), hard=bool(raw.get("hard", False)),
            evidence_level=raw.get("evidence_level", ""), recommendation_en=raw.get("recommendation_en", ""),
            recommendation_bn=raw.get("recommendation_bn", ""),
            sources=[Source(**{k: str(s.get(k) or "") for k in ("key", "citation", "doi", "pmid", "licence", "quote")})
                     for s in raw.get("sources", [])],
            review=f"{review.get('method', raw.get('reviewed_by', ''))}, {review.get('verdict', raw.get('status', ''))}, {review.get('date', '')}".strip(", "),
        ))
    return out


def _matches(rule: Rule, words: list[str]) -> int:
    text = " ".join([rule.id, rule.title_en, rule.title_bn, rule.component.replace("_", " "), rule.recommendation_en,
                     rule.recommendation_bn, *(s.quote for s in rule.sources)]).lower()
    return sum(1 for w in words if w in text)


def build_server(rules: list[Rule]) -> MCPServer:
    by_id = {r.id: r for r in rules}
    server = MCPServer(
        name="happygut-guidelines",
        title="HappyGut cited dietary Rule Cards",
        instructions=(
            "Read-only access to HappyGut's Rule Cards for IBD: structured rules taken from published guidance, each with "
            "its paper (DOI / PMID) and the exact sentence it relies on. Quote sources exactly; never present a food as "
            "'safe' and never give medication advice. Contains no patient data."
        ),
        version="0.1.0",
    )

    @server.tool(annotations=READ_ONLY)
    def search_rules(
        query: str = Field(default="", max_length=200, description="Words to look for (English or Bangla), e.g. 'fat flare' or 'lactose'"),
        component: str | None = Field(default=None, description="e.g. fat, lactose, insoluble_fibre, capsaicin_spice"),
        diagnosis: Diagnosis | None = None,
        state: State | None = None,
        phenotype: Phenotype | None = Field(default=None, description="Only rules for this condition (plus rules for any condition)"),
        limit: int = Field(default=10, ge=1, le=25),
    ) -> RuleSearch:
        """Find Rule Cards by words and filters. Hard safety rules come first, then the best keyword matches."""
        words = [w for w in query.lower().split() if len(w) > 1]
        hits = []
        for r in rules:
            if component and r.component != component:
                continue
            if diagnosis and diagnosis not in r.diagnoses:
                continue
            if state and state not in r.states:
                continue
            if phenotype and phenotype not in r.phenotypes and "any" not in r.phenotypes:
                continue
            score = _matches(r, words) if words else 1
            if score:
                hits.append((r.hard, score, r.severity, r))
        hits.sort(key=lambda h: (not h[0], -h[1], -h[2], h[3].id))
        return RuleSearch(query=query, rules=[h[3] for h in hits[:limit]])

    @server.tool(annotations=READ_ONLY)
    def get_rule(rule_id: str = Field(pattern=r"^RC-[A-Z0-9-]+$")) -> Rule:
        """One Rule Card with its sources and exact quotes."""
        if rule_id not in by_id:
            raise ToolError(f"unknown rule {rule_id}")
        return by_id[rule_id]

    @server.tool(annotations=READ_ONLY)
    def list_sources() -> SourceList:
        """Every paper the Rule Cards cite, with the rules that rely on it."""
        found: dict[str, SourceSummary] = {}
        for r in rules:
            for s in r.sources:
                entry = found.setdefault(s.key, SourceSummary(key=s.key, citation=s.citation, doi=s.doi, pmid=s.pmid,
                                                              licence=s.licence, rules=[], has_quote=False))
                entry.rules.append(r.id)
                entry.has_quote = entry.has_quote or bool(s.quote.strip())
        return SourceList(sources=sorted(found.values(), key=lambda x: (-len(x.rules), x.key)))

    return server


def main() -> None:
    run(lambda: build_server(load_rules(include_drafts=os.environ.get("HAPPYGUT_INCLUDE_DRAFTS") == "1")), __doc__, 8101)


if __name__ == "__main__":
    main()
