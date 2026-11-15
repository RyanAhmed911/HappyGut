"""Deterministic verdict engine (docs/02-architecture.md §3).

The LLM never decides: this module turns knowledge-graph, guideline and personal
evidence into a graded verdict, and records why.
"""

from __future__ import annotations

from typing import Iterable, Mapping

from .config import DEFAULT_CONFIG, EngineConfig
from .models import (
    ComponentAssessment,
    DishEvidence,
    DishVerdict,
    MealVerdict,
    PersonalEvidence,
    Profile,
    RuleCard,
)
from .vocab import Component, Level, Verdict


def _clip(value: float) -> float:
    return max(0.0, min(1.0, value))


def _guideline_score(rule: RuleCard, level: Level, profile: Profile, config: EngineConfig) -> float:
    raw = rule.severity * config.level_weights[level] * config.state_multiplier[profile.state]
    return _clip(raw / config.max_severity)


def _assess_component(
    component: Component,
    level: Level | None,
    profile: Profile,
    rules: Iterable[RuleCard],
    personal: PersonalEvidence | None,
    config: EngineConfig,
) -> ComponentAssessment:
    applicable = [r for r in rules if r.applies(profile, component, level)]
    hard = tuple(r.id for r in applicable if r.hard)
    guideline = max((_guideline_score(r, level, profile, config) for r in applicable), default=0.0)

    personal_score = 0.0
    tolerated = False
    if personal is not None and level is not None and level >= max(Level.LOW, personal.min_level - 1):
        weight = config.level_weights[level]
        strength = _clip((personal.p_trigger - config.personal_neutral) / (1.0 - config.personal_neutral))
        if personal.exposures >= config.min_personal_exposures:
            personal_score = _clip(strength * weight)
            tolerated = personal.p_trigger <= config.tolerance_p_max
        else:
            personal_score = _clip(strength * weight * config.prior_weight)

    if tolerated and not hard:
        guideline *= config.tolerance_discount

    risk = 1.0 if hard else max(guideline, personal_score)
    return ComponentAssessment(
        component=component,
        level=level,
        guideline_score=round(guideline, 4),
        personal_score=round(personal_score, 4),
        risk=round(risk, 4),
        rule_ids=tuple(r.id for r in applicable),
        hard_rule_ids=hard,
        personal=personal if personal_score > 0 or tolerated else None,
        tolerated=tolerated,
    )


def _coverage(dish: DishEvidence) -> float:
    if not dish.components:
        return 0.0
    known = sum(1 for level in dish.components.values() if level is not None)
    return known / len(dish.components)


def _verdict_for_risk(risk: float, config: EngineConfig) -> Verdict:
    if risk > config.trigger_above:
        return Verdict.LIKELY_TRIGGER
    if risk < config.ok_below:
        return Verdict.LIKELY_OK
    return Verdict.CAUTION


def assess_dish(
    dish: DishEvidence,
    profile: Profile,
    rules: Iterable[RuleCard],
    personal: Mapping[Component, PersonalEvidence] | None = None,
    config: EngineConfig = DEFAULT_CONFIG,
) -> DishVerdict:
    """Verdict for one dish, without choosing an alternative."""
    rules = tuple(rules)
    personal = personal or {}
    assessments = tuple(
        _assess_component(c, level, profile, rules, personal.get(c), config)
        for c, level in sorted(dish.components.items(), key=lambda kv: kv[0].value)
    )
    hard_ids = tuple(rid for a in assessments for rid in a.hard_rule_ids)
    risk = max((a.risk for a in assessments), default=0.0)
    guideline = max((a.guideline_score for a in assessments), default=0.0)
    personal_part = max((a.personal_score for a in assessments), default=0.0)
    confidence = round(min(dish.perception_confidence, dish.resolution_confidence, _coverage(dish)), 4)

    if confidence < config.min_confidence:
        verdict, reason = Verdict.NOT_SURE, "low_confidence"
    elif hard_ids:
        verdict, reason = Verdict.LIKELY_TRIGGER, "hard_rule"
    else:
        verdict = _verdict_for_risk(risk, config)
        if verdict == Verdict.LIKELY_OK:
            reason = "no_risk"
        else:
            reason = "personal" if personal_part >= guideline else "guideline"

    evidence = [f"dish:{dish.dish_id}"]
    for a in assessments:
        evidence.extend(a.rule_ids)
        if a.personal is not None:
            evidence.append(f"personal:{a.component.value}")

    return DishVerdict(
        dish_id=dish.dish_id,
        verdict=verdict,
        risk=round(risk, 4),
        confidence=confidence,
        reason=reason,
        components=assessments,
        hard_rule_ids=hard_ids,
        evidence_ids=tuple(dict.fromkeys(evidence)),
        guideline_contribution=round(guideline, 4),
        personal_contribution=round(personal_part, 4),
    )


def _pick_alternative(
    verdict: DishVerdict,
    dish: DishEvidence,
    profile: Profile,
    rules: tuple[RuleCard, ...],
    personal: Mapping[Component, PersonalEvidence],
    pool: Mapping[str, DishEvidence],
    config: EngineConfig,
) -> str | None:
    if verdict.verdict not in (Verdict.CAUTION, Verdict.LIKELY_TRIGGER):
        return None
    best: tuple[float, str] | None = None
    for alt_id in dish.alternatives:
        alt = pool.get(alt_id)
        if alt is None:
            continue
        alt_verdict = assess_dish(alt, profile, rules, personal, config)
        if alt_verdict.verdict != Verdict.LIKELY_OK or alt_verdict.risk >= verdict.risk:
            continue
        if best is None or alt_verdict.risk < best[0]:
            best = (alt_verdict.risk, alt_id)
    return best[1] if best else None


def assess_meal(
    dishes: Iterable[DishEvidence],
    profile: Profile,
    rules: Iterable[RuleCard],
    personal: Mapping[Component, PersonalEvidence] | None = None,
    alternatives_pool: Mapping[str, DishEvidence] | None = None,
    config: EngineConfig = DEFAULT_CONFIG,
) -> MealVerdict:
    """Verdict for a whole meal: each dish is assessed, the most cautious verdict wins."""
    rules = tuple(rules)
    personal = personal or {}
    pool = alternatives_pool or {}
    results = []
    for dish in dishes:
        dv = assess_dish(dish, profile, rules, personal, config)
        alt = _pick_alternative(dv, dish, profile, rules, personal, pool, config)
        if alt is not None:
            dv = DishVerdict(**{**dv.__dict__, "alternative_id": alt})
        results.append(dv)

    if not results:
        return MealVerdict(
            verdict=Verdict.NOT_SURE,
            risk=0.0,
            confidence=0.0,
            dishes=(),
            config_version=config.version,
            notes=("no_dishes",),
        )
    worst = max(results, key=lambda d: (d.verdict.rank, d.risk))
    return MealVerdict(
        verdict=worst.verdict,
        risk=max(d.risk for d in results),
        confidence=min(d.confidence for d in results),
        dishes=tuple(results),
        config_version=config.version,
    )
