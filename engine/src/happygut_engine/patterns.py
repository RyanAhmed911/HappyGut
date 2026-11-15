"""Flare Pattern Finder: which foods and habits are linked to this person's worse days.

A Bayesian N-of-1 comparison (spec 003 FR-013 to FR-016). For each factor we compare how
often a "worse day" follows days with the factor against days without it, inside the
factor's time window. Both rates get Beta posteriors; the link probability is
P(rate after the factor > rate without it + a minimum difference), by seeded Monte Carlo
so results repeat.

Results are patterns ("linked to", "likely contributor"), never proven causes
(Constitution IV). Only food-component results feed the meal verdict.
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Mapping, Sequence

from .models import PersonalEvidence
from .vocab import Component, Level

LIKELY, POSSIBLE, NOT_LINKED, NOT_ENOUGH = "likely_contributor", "possible", "not_linked", "not_enough_data"

# Factor ids. Food components use "food:<component>"; stressful periods use "period:<type>".
LATE_NIGHT, SHORT_SLEEP, POOR_SLEEP = "sleep:late_night", "sleep:short", "sleep:poor_quality"
HIGH_STRESS, MISSED_DOSE = "stress:high", "medication:missed_dose"
PERIOD_TYPES = ("exam", "work", "family", "fasting", "travel", "menstruation", "other")


@dataclass(frozen=True)
class PatternConfig:
    version: str = "patterns-v0.1"
    worse_delta: int = 2  # index points above the person's own recent median
    median_window: int = 14
    min_exposures: int = 3
    min_baseline_days: int = 7
    # "Linked" means worse days follow at least this much more often (in rate), not just "more often":
    # with a dozen factors, tiny differences would otherwise produce false alarms (spec 003 SC-003).
    min_rate_difference: float = 0.10
    overlap_max_prevalence: float = 0.5  # a factor present on most days overlaps everything; don't report it
    likely_above: float = 0.8
    not_linked_below: float = 0.5
    overlap_above: float = 0.7
    # Only high levels count as a food exposure: in Bangladeshi cooking, medium fat, onion / garlic
    # and spice are in most dishes, so "medium or above" is true nearly every day and says nothing.
    food_min_level: Level = Level.HIGH
    short_sleep_hours: float = 6.0
    high_stress_at: int = 3
    # Days after the exposure day in which a worse day counts (0 = the same day).
    windows: Mapping[str, tuple[int, ...]] = field(default_factory=lambda: {
        "food": (0, 1),  # 6-48 h after eating: the same day and the next
        "sleep": (0, 1),  # the day after the night, and the next
        "stress": (0, 1, 2),
        "period": (0, 1),
        "medication": (1, 2, 3),
    })
    prior: tuple[float, float] = (1.0, 3.0)
    baseline_prior: tuple[float, float] = (1.0, 1.0)
    samples: int = 20_000
    seed: int = 7


DEFAULT_PATTERN_CONFIG = PatternConfig()


@dataclass(frozen=True)
class DayRecord:
    """One diary day. ``None`` means the answer was skipped (left out of that analysis)."""

    day: date
    index: int | None = None
    food_reaction: bool = False
    components: Mapping[Component, Level] = field(default_factory=dict)  # highest level eaten that day
    has_food_log: bool = True
    late_night: bool | None = None
    sleep_hours: float | None = None
    sleep_quality: str | None = None  # good | ok | poor
    stress: int | None = None
    period_types: frozenset[str] = frozenset()
    medication: str | None = None  # taken | missed | na
    period_kind: str | None = None  # remission | flare | settling


@dataclass(frozen=True)
class PatternResult:
    factor: str
    group: str  # food | sleep | stress | period | medication
    window_days: tuple[int, ...]
    exposures: int
    hits: int
    baseline_days: int
    baseline_hits: int
    exposed_rate: float
    baseline_rate: float
    probability: float  # P(rate after the factor > rate without it + min_rate_difference)
    ci_low: float
    ci_high: float
    label: str
    overlaps_with: tuple[str, ...] = ()

    def to_personal_evidence(self, min_level: Level = Level.HIGH) -> PersonalEvidence | None:
        if self.group != "food":
            return None
        return PersonalEvidence(
            component=Component(self.factor.split(":", 1)[1]),
            p_trigger=self.probability, exposures=self.exposures, ci_low=self.ci_low, ci_high=self.ci_high,
            min_level=min_level,
        )


# ---------------------------------------------------------------- worse days

def worse_days(days: Sequence[DayRecord], config: PatternConfig = DEFAULT_PATTERN_CONFIG) -> set[date]:
    """Days whose index is well above the person's own recent median, or with a food reaction."""
    out: set[date] = set()
    history: list[int] = []
    for rec in sorted(days, key=lambda r: r.day):
        if rec.food_reaction:
            out.add(rec.day)
        if rec.index is not None:
            recent = history[-config.median_window:]
            if len(recent) >= 3 and rec.index >= statistics.median(recent) + config.worse_delta:
                out.add(rec.day)
            history.append(rec.index)
    return out


# ---------------------------------------------------------------- factors

def exposure(rec: DayRecord, factor: str, config: PatternConfig) -> bool | None:
    """True / False, or None when the day can't be used for this factor."""
    group, _, name = factor.partition(":")
    if group == "food":
        if not rec.has_food_log:
            return None
        level = rec.components.get(Component(name))
        return level is not None and level >= config.food_min_level
    if factor == LATE_NIGHT:
        return rec.late_night
    if factor == SHORT_SLEEP:
        return None if rec.sleep_hours is None else rec.sleep_hours < config.short_sleep_hours
    if factor == POOR_SLEEP:
        return None if rec.sleep_quality is None else rec.sleep_quality == "poor"
    if factor == HIGH_STRESS:
        return None if rec.stress is None else rec.stress >= config.high_stress_at
    if group == "period":
        return name in rec.period_types
    if factor == MISSED_DOSE:
        return None if rec.medication in (None, "na") else rec.medication == "missed"
    raise ValueError(f"unknown factor: {factor}")


def all_factors() -> list[str]:
    return ([f"food:{c.value}" for c in Component]
            + [LATE_NIGHT, SHORT_SLEEP, POOR_SLEEP, HIGH_STRESS]
            + [f"period:{t}" for t in PERIOD_TYPES] + [MISSED_DOSE])


def _posterior(hits: int, n: int, b_hits: int, b_n: int, config: PatternConfig) -> tuple[float, float, float, float, float]:
    a_e, b_e = config.prior[0] + hits, config.prior[1] + (n - hits)
    a_b, b_b = config.baseline_prior[0] + b_hits, config.baseline_prior[1] + (b_n - b_hits)
    rng = random.Random(config.seed)
    draws, above = [], 0
    for _ in range(config.samples):
        e, b = rng.betavariate(a_e, b_e), rng.betavariate(a_b, b_b)
        draws.append(e)
        above += e > b + config.min_rate_difference
    draws.sort()
    return (a_e / (a_e + b_e), a_b / (a_b + b_b), above / config.samples,
            draws[int(0.05 * config.samples)], draws[int(0.95 * config.samples) - 1])


def _label(exposures: int, baseline_days: int, probability: float, config: PatternConfig) -> str:
    # Too few exposures, or (a factor present almost every day) too few days without it to compare.
    if exposures < config.min_exposures or baseline_days < config.min_baseline_days:
        return NOT_ENOUGH
    if probability > config.likely_above:
        return LIKELY
    if probability < config.not_linked_below:
        return NOT_LINKED
    return POSSIBLE


def find_patterns(
    days: Sequence[DayRecord],
    scope: str | None = None,
    factors: Sequence[str] | None = None,
    config: PatternConfig = DEFAULT_PATTERN_CONFIG,
) -> list[PatternResult]:
    """Analyse every factor the person has been exposed to at least once.

    ``scope``: None for all days, or "remission" / "flare" to use only days of that period
    kind as exposure days (worse days are still judged against the whole history).
    Results are sorted: likely contributors first, then by link probability.
    """
    records = sorted(days, key=lambda r: r.day)
    worse = worse_days(records, config)
    logged = {r.day for r in records if r.index is not None or r.food_reaction}
    exposure_days: dict[str, set[date]] = {}
    results: list[PatternResult] = []

    for factor in factors or all_factors():
        group = factor.split(":", 1)[0]
        window = config.windows[group]
        exposed: list[bool] = []
        unexposed: list[bool] = []
        on_days: set[date] = set()
        for rec in records:
            if scope is not None and rec.period_kind != scope:
                continue
            state = exposure(rec, factor, config)
            if state is None:
                continue
            followers = [rec.day + timedelta(days=o) for o in window]
            if not any(f in logged for f in followers):
                continue  # nothing was logged in the window: outcome unknown, not "fine"
            followed = any(f in worse for f in followers)
            if state:
                exposed.append(followed)
                on_days.add(rec.day)
            else:
                unexposed.append(followed)
        if not exposed:
            continue
        exposure_days[factor] = on_days
        e_rate, b_rate, p, lo, hi = _posterior(sum(exposed), len(exposed), sum(unexposed), len(unexposed), config)
        results.append(PatternResult(
            factor=factor, group=group, window_days=tuple(window),
            exposures=len(exposed), hits=sum(exposed), baseline_days=len(unexposed), baseline_hits=sum(unexposed),
            exposed_rate=round(e_rate, 4), baseline_rate=round(b_rate, 4), probability=round(p, 4),
            ci_low=round(lo, 4), ci_high=round(hi, 4), label=_label(len(exposed), len(unexposed), p, config),
        ))

    # Overlap: most of A's exposure days are also B's (late nights during exams).
    total_days = max(1, len({rec.day for rec in records if scope is None or rec.period_kind == scope}))
    with_overlap = []
    for r in results:
        mine = exposure_days[r.factor]
        over = tuple(
            other.factor for other in results
            if other.factor != r.factor and len(mine) >= config.min_exposures
            and len(exposure_days[other.factor]) / total_days <= config.overlap_max_prevalence
            and len(mine & exposure_days[other.factor]) / len(mine) > config.overlap_above
        )
        with_overlap.append(PatternResult(**{**r.__dict__, "overlaps_with": over}))

    order = {LIKELY: 0, POSSIBLE: 1, NOT_LINKED: 2, NOT_ENOUGH: 3}
    with_overlap.sort(key=lambda r: (order[r.label], -r.probability, -r.exposures, r.factor))
    return with_overlap


def personal_evidence(
    results: Sequence[PatternResult], config: PatternConfig = DEFAULT_PATTERN_CONFIG,
) -> dict[Component, PersonalEvidence]:
    """Food-component results in the form the verdict engine takes (spec 003 FR-020)."""
    out = {}
    for r in results:
        ev = r.to_personal_evidence(config.food_min_level)
        if ev is not None:
            out[ev.component] = ev
    return out
