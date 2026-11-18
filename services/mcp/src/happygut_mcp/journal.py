"""happygut-journal: read-only MCP server over ONE patient's own HappyGut records, with their consent.

Consent is the patient's own sign-in: the server only works with a session token the patient
created and chose to hand to an AI client (for example to let their clinician's assistant read
their summary before a visit). It can read nothing else, and it can change nothing.

Tools
- get_overview:     the pre-visit summary (symptom score, periods, likely contributors, flare-risk
                    outlook, weight, medicines as entered, upcoming tests)
- get_recent_days:  day-by-day diary scores, stools, pain, sleep, stress and dose logging (up to 30 days)
- get_patterns:     the Flare Pattern Finder results, overall or within remission or flares

What it leaves out on purpose: the patient's name, free-text notes and meal photos. Patterns are
"linked to", never "caused". No medication advice.

Run
    HAPPYGUT_API_URL=https://… HAPPYGUT_PATIENT_TOKEN=… happygut-journal          # stdio
    happygut-journal --http --port 8103    # Streamable HTTP, also requires MCP_BEARER_TOKEN
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Literal

import httpx
from pydantic import BaseModel, Field

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from .common import READ_ONLY_REMOTE, run

NOTE = "Patterns are links in this patient's own diary, not proven causes. HappyGut gives no medication advice."


class Overview(BaseModel):
    period: dict = Field(description="from / to / days logged")
    diagnosis: str
    phenotypes: list[str]
    current_state: str
    index: dict = Field(description="Name (HBI or SCCAI), average, worst, days with blood")
    doses: dict
    periods: list[dict]
    likely_contributors: list[dict]
    flare_risk: dict
    weight: dict | None
    medicines: list[dict] = Field(description="As entered by the patient")
    upcoming_tests: list[dict]
    sample_data: bool = Field(description="True for HappyGut's test accounts, which hold synthetic records")
    note: str = NOTE


class RecentDays(BaseModel):
    days: list[dict]
    sample_data: bool
    note: str = "Free-text notes and meal photos are not shared through this server."


class Patterns(BaseModel):
    scope: str
    enough_data: bool
    days_logged: int
    results: list[dict]
    note: str = NOTE


def _client_from_env() -> httpx.Client:
    url, token = os.environ.get("HAPPYGUT_API_URL", ""), os.environ.get("HAPPYGUT_PATIENT_TOKEN", "")
    if not url or not token:
        raise SystemExit("Set HAPPYGUT_API_URL and HAPPYGUT_PATIENT_TOKEN (the patient's own sign-in token).")
    return httpx.Client(base_url=url.rstrip("/"), headers={"Authorization": f"Bearer {token}"}, timeout=20)


def build_server(client: Callable[[], httpx.Client]) -> MCPServer:
    def get(path: str, **params) -> dict:
        with client() as c:
            r = c.get(path, params=params)
        if r.status_code == 401:
            raise ToolError("The patient's sign-in has expired or was withdrawn; ask them for a new one.")
        if r.status_code >= 400:
            raise ToolError(f"HappyGut returned {r.status_code}")
        return r.json()

    server = MCPServer(
        name="happygut-journal",
        title="HappyGut patient journal (read-only, with the patient's consent)",
        instructions=(
            "Read-only access to ONE patient's own HappyGut records, shared by the patient. Use it to prepare for a visit "
            "or to answer the patient's questions about their own diary. Describe patterns as 'linked to', never 'caused'. "
            "Never advise starting, stopping or changing a medicine. Warning signs (heavy bleeding, fever with abdominal "
            "pain, signs of obstruction, severe dehydration) need a doctor."
        ),
        version="0.1.0",
    )

    @server.tool(annotations=READ_ONLY_REMOTE)
    def get_overview(days: int = Field(default=90, ge=14, le=180, description="How far back to summarise")) -> Overview:
        """The patient's pre-visit summary for the last N days, without their name or notes."""
        r = get("/v1/reports/previsit", days=days)
        weight = r.get("weight")
        return Overview(
            period={"from": r["from"], "to": r["to"], "days_logged": r["days_logged"], "days_in_range": r["days_in_range"]},
            diagnosis=r["patient"]["diagnosis"], phenotypes=r["patient"]["phenotypes"], current_state=r["patient"]["current_state"],
            index={"name": r["index_name"], "average": r["avg_index"], "worst": r["worst_index"], "days_with_blood": r["days_with_blood"]},
            doses=r["adherence"],
            periods=[{k: p[k] for k in ("kind", "start", "end", "days", "status") if k in p} for p in r["periods"]],
            likely_contributors=[{k: c[k] for k in ("factor", "label", "exposures", "hits", "baseline_days", "baseline_hits")}
                                 for c in r["contributors"]],
            flare_risk={"level": r["risk"]["level"], "score": r["risk"]["score"],
                        "drivers": [{k: d.get(k) for k in ("code", "factor", "points")} for d in r["risk"].get("drivers", [])]},
            weight=None if not weight else {"latest": weight["latest"], "loss": weight["loss"], "weigh_ins": weight["weigh_ins"]},
            medicines=r.get("medications", []),
            upcoming_tests=[{k: a[k] for k in ("kind", "date", "time")} for a in r.get("appointments", [])],
            sample_data=r["is_synthetic"],
        )

    @server.tool(annotations=READ_ONLY_REMOTE)
    def get_recent_days(days: int = Field(default=14, ge=1, le=30)) -> RecentDays:
        """Day-by-day diary values for the last N days (no notes, no photos)."""
        r = get("/v1/diary/days", limit=days)
        keep = ("date", "index", "stools", "pain", "blood", "sleep_hours", "late_night", "stress", "medication", "period_kind",
                "tags", "food_reaction")
        return RecentDays(days=[{k: d.get(k) for k in keep} for d in r["days"]], sample_data=r["is_synthetic"])

    @server.tool(annotations=READ_ONLY_REMOTE)
    def get_patterns(scope: Literal["all", "remission", "flare"] = "all") -> Patterns:
        """What the patient's own diary links to their worse days, with the counts behind each link."""
        r = get("/v1/insights/patterns", scope=scope)
        keep = ("factor", "group", "label", "exposures", "hits", "baseline_days", "baseline_hits", "probability", "overlaps_with")
        return Patterns(scope=scope, enough_data=r["enough_data"], days_logged=r["days_logged"],
                        results=[{k: x.get(k) for k in keep} for x in r["results"]])

    return server


def main() -> None:
    run(lambda: build_server(_client_from_env), __doc__, 8103)


if __name__ == "__main__":
    main()
