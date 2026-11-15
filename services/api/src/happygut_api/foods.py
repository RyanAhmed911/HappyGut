"""Personal food guide and meal ideas, computed by the verdict engine (no model involved).

- ``guide``: every dish in the knowledge layer with this person's verdict, so they can see
  what is likely OK, what needs caution and what is a likely trigger for them.
- ``plan``: a week of meal ideas built only from dishes the engine rates "likely OK" for
  this person right now. They are ideas, not a prescription, and never called "safe".
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Mapping

from happygut_engine import Component, PersonalEvidence, Profile, Verdict, assess_meal

from .knowledge import MemoryKnowledge

BREAKFAST = ("bread", "egg", "staple")
MAINS = ("fish", "curry", "stew", "egg")
SIDES = ("dal", "vegetable", "bhorta")
LIGHT = ("snack", "dairy", "sweet", "sweet_snack", "drink")
RICE = "dish.plain_rice"


def guide(knowledge: MemoryKnowledge, profile: Profile, personal: Mapping[Component, PersonalEvidence]) -> list[dict]:
    rules, pool = knowledge.rules(), knowledge.alternatives_pool()
    out = []
    for dish in knowledge.graph.dishes.values():
        meal = assess_meal([dish.to_evidence()], profile, rules, personal, pool)
        v = meal.dishes[0]
        top = sorted((a for a in v.components if a.risk > 0), key=lambda a: -a.risk)[:3]
        alt = None
        if v.alternative_id:
            en, bn = knowledge.names(v.alternative_id)
            alt = {"dish_id": v.alternative_id, "name_en": en, "name_bn": bn}
        out.append({
            "dish_id": dish.id, "name_en": dish.name_en, "name_bn": dish.name_bn,
            "category": dish.raw.get("category", "other"), "verdict": v.verdict.value, "risk": v.risk, "reason": v.reason,
            "components": [{"component": a.component.value, "level": a.level.name.lower() if a.level is not None else "unknown",
                            "source": "personal" if a.personal_score >= a.guideline_score and a.personal_score > 0 else "guideline"}
                           for a in top],
            "alternative": alt,
        })
    order = {Verdict.LIKELY_OK.value: 0, Verdict.CAUTION.value: 1, Verdict.LIKELY_TRIGGER.value: 2, Verdict.NOT_SURE.value: 3}
    out.sort(key=lambda d: (order[d["verdict"]], d["risk"], d["name_en"]))
    return out


def plan(entries: list[dict], start: date, seed: str, days: int = 7) -> dict:
    """Meal ideas from the "likely OK" entries of ``guide``. Deterministic for a given seed."""
    ok = [e for e in entries if e["verdict"] == Verdict.LIKELY_OK.value]
    by_cat: dict[str, list[dict]] = {}
    for e in ok:
        by_cat.setdefault(e["category"], []).append(e)
    rng = random.Random(seed)

    def pool(categories: tuple[str, ...], exclude: set[str] = frozenset()) -> list[dict]:
        items = [e for c in categories for e in by_cat.get(c, []) if e["dish_id"] not in exclude]
        rng.shuffle(items)
        return items

    rice = next((e for e in ok if e["dish_id"] == RICE), None)
    breakfasts, mains, sides, lights = pool(BREAKFAST, {RICE}), pool(MAINS), pool(SIDES), pool(LIGHT)
    one_pot = pool(("rice_dish",))  # khichuri and the like: a meal on their own

    def slim(e: dict) -> dict:
        return {"dish_id": e["dish_id"], "name_en": e["name_en"], "name_bn": e["name_bn"]}

    def take(items: list[dict], i: int) -> list[dict]:
        return [slim(items[i % len(items)])] if items else []

    out_days = []
    m = s = 0
    for d in range(days):
        meals = {"breakfast": take(breakfasts, d) + (take(lights, d) if lights and d % 2 == 0 else [])}
        for slot in ("lunch", "dinner"):
            if one_pot and (d + (slot == "dinner")) % 4 == 3:
                meals[slot] = take(one_pot, d) + take(sides, s)
            else:
                meals[slot] = ([slim(rice)] if rice else []) + take(mains, m) + take(sides, s)
                m += 1
            s += 1
        out_days.append({"date": (start + timedelta(days=d)).isoformat(), "meals": meals})
    enough = bool(mains) and bool(breakfasts)
    return {"days": out_days if enough else [], "pool_size": len(ok), "enough": enough}
