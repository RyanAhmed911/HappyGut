"""happygut-evals: read-only MCP server over HappyGut's measured evaluation results.

Tools
- get_results:        the latest evaluation (evals/summary.json): Pattern Finder on a simulated cohort,
                      red-flag suite, verdict rules, dish names; always labelled with its limits
- pattern_recovery:   the Pattern Finder's results at one diary length (21-120 days)
- check_red_flags:    run HappyGut's red-flag sentinel on a message (deterministic; nothing is stored)

Results on the cohort come from simulated patients and are always reported as such. No patient data.

Run
    happygut-evals                       # stdio
    happygut-evals --http --port 8102    # Streamable HTTP, requires MCP_BEARER_TOKEN
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from happygut_engine import check_red_flags as sentinel
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from .common import READ_ONLY, run

SUMMARY = Path(__file__).resolve().parents[4] / "evals" / "summary.json"
LIMITS = ("Pattern Finder numbers come from simulated patients with injected hidden contributors; the red-flag suite was "
          "written by the team. These are not results on real patients or a clinical evaluation. Photo recognition, "
          "agreement with dietitian ratings and end-to-end response time have not been measured.")


class Results(BaseModel):
    date: str
    simulated_cohort: bool
    limits: str = LIMITS
    pattern_finder: dict = Field(description="Found / false reports at the longest diary length, plus recall by kind of factor")
    red_flags: dict
    verdicts: dict
    dish_names: dict
    knowledge: dict
    reproduce: str = "cd services/api && uv run python -m happygut_api.evaluate"


class Recovery(BaseModel):
    days: int
    patients: int
    true_contributors: int
    found: int
    recall: float | None
    false_reports: int
    companion_reports: int
    precision: float | None = Field(description="Found / (found + false reports), companion reports set aside")
    precision_counting_companions: float | None
    simulated: bool = True


class RedFlagCheck(BaseModel):
    triggered: bool
    categories: list[str]
    action: str


def load_summary(path: Path = SUMMARY) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_server(summary: dict) -> MCPServer:
    cohort = summary["cohort"]
    horizons = {int(h): r for h, r in cohort["by_horizon"].items()}
    server = MCPServer(
        name="happygut-evals",
        title="HappyGut evaluation results",
        instructions=(
            "Read-only access to HappyGut's measured evaluation results. Always repeat the limits: Pattern Finder results "
            "come from simulated patients, and the red-flag suite is a development set. Contains no patient data."
        ),
        version="0.1.0",
    )

    @server.tool(annotations=READ_ONLY)
    def get_results() -> Results:
        """The latest evaluation run, with its limits."""
        last = horizons[max(horizons)]
        return Results(
            date=summary["date"], simulated_cohort=summary["simulated_cohort"],
            pattern_finder={"patients": cohort["patients"], "days": max(horizons), "found": last["found"],
                            "true_contributors": last["true_contributors"], "false_reports": last["false_reports"],
                            "companion_reports": last["related_reports"], "recall_by_kind": last["recall_by_group"]},
            red_flags={k: summary["red_flags"][k] for k in ("phrases", "caught", "ordinary_messages", "by_language")},
            verdicts={k: summary["verdicts"][k] for k in ("dishes", "assessments", "identical_on_repeat",
                                                          "caution_or_trigger_without_a_rule", "stricture_rule", "by_profile")},
            dish_names={k: {"names": v["names"], "resolved_to_own_dish": v["resolved_to_own_dish"]} for k, v in summary["dish_names"].items()},
            knowledge=summary["knowledge"],
        )

    @server.tool(annotations=READ_ONLY)
    def pattern_recovery(days: int = Field(description="Diary length: 21, 30, 60, 90 or 120")) -> Recovery:
        """How many hidden contributors the Pattern Finder found after this many days of diary (simulated patients)."""
        if days not in horizons:
            raise ToolError(f"no result for {days} days; available: {sorted(horizons)}")
        r = horizons[days]
        return Recovery(days=days, patients=cohort["patients"], true_contributors=r["true_contributors"], found=r["found"],
                        recall=r["recall"], false_reports=r["false_reports"], companion_reports=r["related_reports"],
                        precision=r["precision"], precision_counting_companions=r["precision_strict"])

    @server.tool(annotations=READ_ONLY)
    def check_red_flags(text: str = Field(min_length=1, max_length=1000, description="A message in English, Bangla or Bangla in English letters")) -> RedFlagCheck:
        """Run HappyGut's red-flag sentinel. Deterministic; nothing is stored."""
        result = sentinel(text)
        return RedFlagCheck(
            triggered=result.triggered, categories=list(result.categories),
            action=("Stop diet advice and direct the person to a doctor or emergency care." if result.triggered
                    else "No warning sign found. This check does not replace medical judgement."),
        )

    return server


def main() -> None:
    run(lambda: build_server(load_summary()), __doc__, 8102)


if __name__ == "__main__":
    main()
