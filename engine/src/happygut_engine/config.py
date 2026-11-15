"""Versioned engine parameters. Change values here only, never inline in the algorithm."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .vocab import DiseaseState, Level


@dataclass(frozen=True)
class EngineConfig:
    version: str = "engine-v0.2"
    level_weights: Mapping[Level, float] = field(
        default_factory=lambda: MappingProxyType(
            {Level.NONE: 0.0, Level.LOW: 0.4, Level.MEDIUM: 0.7, Level.HIGH: 1.0}
        )
    )
    state_multiplier: Mapping[DiseaseState, float] = field(
        default_factory=lambda: MappingProxyType({DiseaseState.REMISSION: 1.0, DiseaseState.FLARE: 1.3})
    )
    max_severity: int = 3
    # Personal evidence
    # p_trigger is P(symptom rate after the component > rate without it), so 0.5 means "no evidence
    # either way". Personal strength rescales it: 0 at the neutral point, 1 at certainty.
    personal_neutral: float = 0.5
    min_personal_exposures: int = 3
    prior_weight: float = 0.5  # weight of personal evidence with fewer than min exposures
    tolerance_p_max: float = 0.2  # p_trigger at or below this, with enough exposures, counts as "tolerated"
    tolerance_discount: float = 0.6  # guideline score multiplier for tolerated components (never for hard rules)
    # Thresholds
    ok_below: float = 0.35
    trigger_above: float = 0.65
    min_confidence: float = 0.5


DEFAULT_CONFIG = EngineConfig()
