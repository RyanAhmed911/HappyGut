"""Scheduled jobs, called by n8n (n8n/workflows). They return aggregate counts only: no names, ids or records.

- nightly:   refresh every patient's insights for the new day and count what needs attention
- selfcheck: run the deterministic safety checks on the live backend (red-flag suite, verdict
             reproducibility, the stricture rule, dish names) so a broken deployment is noticed
"""

from __future__ import annotations

import hmac
import time

from .insights import Insights
from .knowledge import MemoryKnowledge
from .store import NotSupported, Store

MIN_TOKEN = 24


def authorised(header: str | None, token: str) -> bool:
    return bool(token) and len(token) >= MIN_TOKEN and hmac.compare_digest((header or "").encode(), f"Bearer {token}".encode())


async def nightly(store: Store, insights: Insights) -> dict:
    started = time.perf_counter()
    today = insights.today()
    counts = {"patients": 0, "diary_filled_today": 0, "in_flare": 0, "high_flare_risk": 0, "weight_notices": 0,
              "doses_due_today": 0, "doses_ticked_today": 0, "skipped": 0}
    from .care import doses_for

    for patient in await store.all_patients():
        counts["patients"] += 1
        try:
            periods = await insights.periods(patient)
            risk = await insights.flare_risk(patient)
            weight = await insights.weight(patient)
            counts["diary_filled_today"] += await store.get_diary(patient.id, today) is not None
            counts["in_flare"] += periods["current_state"] == "flare"
            counts["high_flare_risk"] += risk["level"] == "high"
            counts["weight_notices"] += weight["loss"] is not None
            doses = doses_for(await store.list_medications(patient.id), today, await store.doses_taken(patient.id, today))
            counts["doses_due_today"] += len(doses)
            counts["doses_ticked_today"] += sum(d["taken"] for d in doses)
        except NotSupported:
            counts["skipped"] += 1
    return {"ok": True, "date": today.isoformat(), "counts": counts, "ms": round((time.perf_counter() - started) * 1000)}


def selfcheck(knowledge: MemoryKnowledge) -> dict:
    from . import evaluate

    started = time.perf_counter()
    flags = evaluate.red_flags()
    verdicts = evaluate.verdicts(knowledge)
    names = evaluate.dish_names(knowledge)
    checks = {
        "red_flags": {"passed": not flags["missed"] and not flags["false_alarms"] and not flags["wrong_category"],
                      "caught": flags["caught"], "phrases": flags["phrases"], "false_alarms": len(flags["false_alarms"])},
        "verdicts_reproducible": {"passed": verdicts["identical_on_repeat"] == verdicts["assessments"],
                                  "identical": verdicts["identical_on_repeat"], "of": verdicts["assessments"]},
        "every_warning_cites_a_rule": {"passed": verdicts["caution_or_trigger_without_a_rule"] == 0,
                                       "uncited": verdicts["caution_or_trigger_without_a_rule"]},
        "stricture_rule": {"passed": not verdicts["stricture_rule"]["not_rated_likely_trigger"],
                           "rated": verdicts["stricture_rule"]["rated_likely_trigger"],
                           "of": verdicts["stricture_rule"]["dishes_with_fibre_skins_seeds_nuts"]},
        "dish_names": {"passed": all(v["names"] == v["resolved_to_own_dish"] for v in names.values()),
                       "wrong": sum(v["names"] - v["resolved_to_own_dish"] for v in names.values())},
    }
    return {"passed": all(c["passed"] for c in checks.values()), "checks": checks,
            "ms": round((time.perf_counter() - started) * 1000)}
