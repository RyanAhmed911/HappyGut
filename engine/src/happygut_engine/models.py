"""Inputs and outputs of the verdict engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .vocab import Component, DiseaseState, Diagnosis, Level, Verdict


@dataclass(frozen=True)
class Profile:
    diagnosis: Diagnosis
    state: DiseaseState
    phenotypes: frozenset[str] = frozenset()


@dataclass(frozen=True)
class RuleCard:
    id: str
    component: Component
    min_level: Level
    severity: int  # 0 none · 1 mild · 2 moderate · 3 strong
    diagnoses: frozenset[Diagnosis] = frozenset({Diagnosis.CD, Diagnosis.UC})
    phenotypes: frozenset[str] = frozenset()  # empty = applies to any phenotype
    states: frozenset[DiseaseState] = frozenset({DiseaseState.REMISSION, DiseaseState.FLARE})
    hard: bool = False

    def __post_init__(self) -> None:
        if not 0 <= self.severity <= 3:
            raise ValueError(f"{self.id}: severity must be 0-3")
        if self.min_level == Level.NONE:
            raise ValueError(f"{self.id}: min_level must be at least LOW")

    def applies(self, profile: Profile, component: Component, level: Level | None) -> bool:
        if component != self.component or level is None or level < self.min_level:
            return False
        if profile.diagnosis not in self.diagnoses or profile.state not in self.states:
            return False
        return not self.phenotypes or bool(self.phenotypes & profile.phenotypes)


@dataclass(frozen=True)
class PersonalEvidence:
    """What Trigger Discovery has learned about one component for one patient."""

    component: Component
    p_trigger: float  # probability this component is a trigger for the patient
    exposures: int
    ci_low: float = 0.0
    ci_high: float = 1.0
    # The level the evidence was learned at. The Pattern Finder learns from high-level exposures, so
    # the evidence counts at that level and one step below (at that step's lower weight), not further.
    min_level: Level = Level.LOW


@dataclass(frozen=True)
class DishEvidence:
    dish_id: str
    components: Mapping[Component, Level | None]  # None = unknown level
    perception_confidence: float = 1.0
    resolution_confidence: float = 1.0
    alternatives: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComponentAssessment:
    component: Component
    level: Level | None
    guideline_score: float
    personal_score: float
    risk: float
    rule_ids: tuple[str, ...]
    hard_rule_ids: tuple[str, ...]
    personal: PersonalEvidence | None
    tolerated: bool


@dataclass(frozen=True)
class DishVerdict:
    dish_id: str
    verdict: Verdict
    risk: float
    confidence: float
    reason: str  # hard_rule | guideline | personal | low_confidence | no_risk
    components: tuple[ComponentAssessment, ...]
    hard_rule_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    guideline_contribution: float
    personal_contribution: float
    alternative_id: str | None = None


@dataclass(frozen=True)
class MealVerdict:
    verdict: Verdict
    risk: float
    confidence: float
    dishes: tuple[DishVerdict, ...]
    config_version: str
    notes: tuple[str, ...] = field(default_factory=tuple)
