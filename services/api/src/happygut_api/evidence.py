"""Evidence packet: the only information the explanation model may use (Constitution IV).

Every item has an ID the explanation must cite: ``dish:<dish_id>`` for composition,
Rule Card IDs for guideline evidence and ``personal:<component>`` for the patient's history.
The packet carries no verdict label (plan decision MC4); the app shows the engine's label.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from happygut_engine import DishVerdict, Level, Verdict

from . import i18n
from .knowledge import Knowledge

EXPLAINED = (Verdict.LIKELY_OK, Verdict.CAUTION, Verdict.LIKELY_TRIGGER)


@dataclass
class DishContext:
    """One perceived item after resolution and verdict."""

    perceived_name: str
    verdict: DishVerdict
    resolved: bool
    name: str  # in the patient's language
    alternative_name: str | None = None
    evidence: list[dict] = field(default_factory=list)

    @property
    def dish_id(self) -> str:
        return self.verdict.dish_id

    @property
    def evidence_ids(self) -> set[str]:
        return {e["id"] for e in self.evidence}

    @property
    def explainable(self) -> bool:
        return self.resolved and self.verdict.verdict in EXPLAINED


def _level_word(level: Level | None) -> str:
    return "unknown" if level is None else level.name.lower()


def build_evidence(ctx: DishContext, knowledge: Knowledge, lang: str) -> list[dict]:
    v = ctx.verdict
    if not ctx.resolved:
        return []
    notable = [a for a in v.components if a.level is not None and a.level >= Level.MEDIUM]
    composition = ", ".join(f"{i18n.t(lang, 'component.' + a.component.value)} ({_level_word(a.level)})" for a in notable)
    items: list[dict] = [{
        "id": f"dish:{v.dish_id}",
        "type": "composition",
        "text": f"Typical recipe of {ctx.name}: {composition or 'no component at medium or high level'}.",
        "components": [{"component": a.component.value, "level": _level_word(a.level)} for a in notable],
    }]
    seen: set[str] = set()
    for a in sorted(v.components, key=lambda a: -a.risk):
        for rule_id in a.rule_ids:
            if rule_id in seen:
                continue
            seen.add(rule_id)
            ref = knowledge.rule_ref(rule_id)
            items.append({
                "id": rule_id,
                "type": "guideline",
                "component": a.component.value,
                "title": ref.title_bn if lang == "bn" else ref.title_en,
                "recommendation": ref.recommendation_bn if lang == "bn" else ref.recommendation_en,
                "strict_rule": ref.hard,
                "sources": [s.citation for s in ref.sources],
            })
        if a.personal is not None:
            p = a.personal
            items.append({
                "id": f"personal:{a.component.value}",
                "type": "personal",
                "component": a.component.value,
                "exposures": p.exposures,
                "probability": round(p.p_trigger, 2),
                "tolerated": a.tolerated,
                "text": (
                    f"In this person's own diary, {i18n.t(lang, 'component.' + a.component.value)} "
                    + ("has rarely been followed by symptoms" if a.tolerated
                       else "has often been followed by symptoms" if p.p_trigger > 0.8
                       else "may be linked to symptoms, but it isn't clear yet")
                    + f" ({p.exposures} exposures, linked with probability {p.p_trigger:.2f})."
                ),
            })
    return items


def packet(dishes: list[DishContext]) -> dict:
    return {
        "dishes": [
            {
                "dish_id": d.dish_id,
                "name": d.name,
                "main_reason": d.verdict.reason,  # hard_rule | guideline | personal | no_risk
                "evidence": d.evidence,
                "alternative": d.alternative_name,
            }
            for d in dishes
            if d.explainable
        ]
    }
