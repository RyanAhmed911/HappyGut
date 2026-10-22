"""Personal Trigger Discovery: Bayesian N-of-1 analysis of meals and symptoms.

For one patient and one food component, compare how often symptoms follow meals
that contain the component (6-48 h later) with how often they follow meals that
don't. Both rates get Beta posteriors; the trigger probability is
P(exposed rate > baseline rate), estimated by seeded Monte Carlo so results are
reproducible.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Mapping, Sequence

from .models import PersonalEvidence
from .vocab import Component, Level


@dataclass(frozen=True)
class MealExposure:
    time: datetime
    components: Mapping[Component, Level | None]


@dataclass(frozen=True)
class SymptomEvent:
    """A symptom rise, e.g. an HBI/SCCAI increase or a reported bad gut day."""

    time: datetime


@dataclass(frozen=True)
class TriggerPosterior:
    component: Component
    exposures: int
    hits: int
    baseline_meals: int
    baseline_hits: int
    exposed_rate: float  # posterior mean
    baseline_rate: float  # posterior mean
    p_trigger: float  # P(exposed rate > baseline rate)
    ci_low: float  # 90% credible interval of the exposed rate
    ci_high: float
    likely_trigger: bool

    def to_personal_evidence(self) -> PersonalEvidence:
        return PersonalEvidence(
            component=self.component,
            p_trigger=self.p_trigger,
            exposures=self.exposures,
            ci_low=self.ci_low,
            ci_high=self.ci_high,
        )


def exposure_outcomes(
    meals: Iterable[MealExposure],
    symptoms: Sequence[SymptomEvent],
    component: Component,
    min_level: Level = Level.MEDIUM,
    window: tuple[timedelta, timedelta] = (timedelta(hours=6), timedelta(hours=48)),
) -> tuple[list[bool], list[bool]]:
    """Split meals into exposed / unexposed and record whether symptoms followed each one."""
    start, end = window
    times = sorted(s.time for s in symptoms)
    exposed: list[bool] = []
    unexposed: list[bool] = []
    for meal in meals:
        followed = any(meal.time + start < t <= meal.time + end for t in times)
        level = meal.components.get(component)
        if level is None and component in meal.components:
            continue  # unknown level: neither exposed nor clean
        if level is not None and level >= min_level:
            exposed.append(followed)
        else:
            unexposed.append(followed)
    return exposed, unexposed


def trigger_posterior(
    component: Component,
    exposed: Sequence[bool],
    unexposed: Sequence[bool],
    prior: tuple[float, float] = (1.0, 3.0),
    baseline_prior: tuple[float, float] = (1.0, 1.0),
    min_exposures: int = 3,
    threshold: float = 0.8,
    samples: int = 20_000,
    seed: int = 7,
) -> TriggerPosterior:
    hits, n = sum(exposed), len(exposed)
    b_hits, b_n = sum(unexposed), len(unexposed)
    a_e, b_e = prior[0] + hits, prior[1] + (n - hits)
    a_b, b_b = baseline_prior[0] + b_hits, baseline_prior[1] + (b_n - b_hits)

    rng = random.Random(seed)
    draws = []
    above = 0
    for _ in range(samples):
        theta_e = rng.betavariate(a_e, b_e)
        theta_b = rng.betavariate(a_b, b_b)
        draws.append(theta_e)
        above += theta_e > theta_b
    draws.sort()
    p = above / samples
    return TriggerPosterior(
        component=component,
        exposures=n,
        hits=hits,
        baseline_meals=b_n,
        baseline_hits=b_hits,
        exposed_rate=round(a_e / (a_e + b_e), 4),
        baseline_rate=round(a_b / (a_b + b_b), 4),
        p_trigger=round(p, 4),
        ci_low=round(draws[int(0.05 * samples)], 4),
        ci_high=round(draws[int(0.95 * samples) - 1], 4),
        likely_trigger=n >= min_exposures and p > threshold,
    )


def discover_triggers(
    meals: Sequence[MealExposure],
    symptoms: Sequence[SymptomEvent],
    components: Iterable[Component] = tuple(Component),
    **kwargs,
) -> dict[Component, TriggerPosterior]:
    """Run trigger_posterior for every component the patient has eaten at least once."""
    results = {}
    for component in components:
        exposed, unexposed = exposure_outcomes(meals, symptoms, component)
        if exposed:
            results[component] = trigger_posterior(component, exposed, unexposed, **kwargs)
    return results
