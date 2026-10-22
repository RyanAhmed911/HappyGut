"""HappyGut engine: deterministic verdicts, red-flag sentinel and Trigger Discovery."""

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
from .redflag import RedFlagResult, check_red_flags
from .triggers import (
    MealExposure,
    SymptomEvent,
    TriggerPosterior,
    discover_triggers,
    exposure_outcomes,
    trigger_posterior,
)
from .verdict import assess_dish, assess_meal
from .vocab import Component, DiseaseState, Diagnosis, Level, Verdict

__all__ = [
    "DEFAULT_CONFIG", "EngineConfig", "ComponentAssessment", "DishEvidence", "DishVerdict",
    "MealVerdict", "PersonalEvidence", "Profile", "RuleCard", "RedFlagResult", "check_red_flags",
    "MealExposure", "SymptomEvent", "TriggerPosterior", "discover_triggers", "exposure_outcomes",
    "trigger_posterior", "assess_dish", "assess_meal", "Component", "DiseaseState", "Diagnosis",
    "Level", "Verdict",
]
