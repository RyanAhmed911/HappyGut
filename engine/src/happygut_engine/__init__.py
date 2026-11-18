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
from .flare_risk import RiskDriver, RiskOutlook, flare_risk
from .indices import THRESHOLDS, DiaryItems, IndexScore, hbi, index_for, index_name, sccai
from .patterns import DayRecord, PatternResult, exposure, find_patterns, personal_evidence, worse_days
from .periods import ManualFlare, Period, current_kind, detect_periods, kind_by_day
from .redflag import RedFlagResult, check_red_flags
from .sleep import is_late_night, sleep_hours, usual_bedtime
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
from .weight import (
    DEFAULT_WEIGHT_CONFIG,
    WeightChange,
    WeightConfig,
    WeightEntry,
    WeightLoss,
    WeightTrend,
    valid_weight,
    weight_trend,
)

__all__ = [
    "DEFAULT_CONFIG", "EngineConfig", "ComponentAssessment", "DishEvidence", "DishVerdict",
    "MealVerdict", "PersonalEvidence", "Profile", "RuleCard", "RedFlagResult", "check_red_flags",
    "MealExposure", "SymptomEvent", "TriggerPosterior", "discover_triggers", "exposure_outcomes",
    "trigger_posterior", "assess_dish", "assess_meal", "Component", "DiseaseState", "Diagnosis",
    "Level", "Verdict",
    "RiskDriver", "RiskOutlook", "flare_risk", "THRESHOLDS", "DiaryItems", "IndexScore", "hbi", "index_for",
    "index_name", "sccai", "DayRecord", "PatternResult", "exposure", "find_patterns", "personal_evidence", "worse_days",
    "ManualFlare", "Period", "current_kind", "detect_periods", "kind_by_day", "is_late_night", "sleep_hours", "usual_bedtime",
    "DEFAULT_WEIGHT_CONFIG", "WeightChange", "WeightConfig", "WeightEntry", "WeightLoss", "WeightTrend", "valid_weight",
    "weight_trend",
]
