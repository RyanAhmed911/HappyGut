"""Controlled vocabulary shared by the engine, the knowledge seeds and the API."""

from __future__ import annotations

from enum import Enum, IntEnum


class Component(str, Enum):
    """Gut-relevant food components. Seeds may only use these keys."""

    FAT = "fat"
    INSOLUBLE_FIBRE = "insoluble_fibre"
    LACTOSE = "lactose"
    FRUCTANS = "fructans"
    GOS = "gos"
    POLYOLS = "polyols"
    EXCESS_FRUCTOSE = "excess_fructose"
    CAPSAICIN_SPICE = "capsaicin_spice"
    ALCOHOL = "alcohol"
    CAFFEINE = "caffeine"
    SKINS_SEEDS_NUTS = "skins_seeds_nuts"
    RED_PROCESSED_MEAT = "red_processed_meat"
    EMULSIFIERS = "emulsifiers"


class Level(IntEnum):
    """How much of a component a typical portion contains. Unknown is represented as ``None``."""

    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3

    @classmethod
    def parse(cls, value: str | None) -> "Level | None":
        if value is None or value == "unknown":
            return None
        return cls[value.upper()]


class Verdict(str, Enum):
    LIKELY_OK = "likely_ok"
    CAUTION = "caution"
    LIKELY_TRIGGER = "likely_trigger"
    NOT_SURE = "not_sure"

    @property
    def emoji(self) -> str:
        return {"likely_ok": "🟢", "caution": "🟡", "likely_trigger": "🔴", "not_sure": "⚪"}[self.value]

    @property
    def rank(self) -> int:
        """Ordering used to combine dishes into a meal verdict (higher = more cautious)."""
        return {"likely_ok": 0, "not_sure": 1, "caution": 2, "likely_trigger": 3}[self.value]


class Diagnosis(str, Enum):
    CD = "CD"  # Crohn's disease
    UC = "UC"  # ulcerative colitis


class DiseaseState(str, Enum):
    REMISSION = "remission"
    FLARE = "flare"


# Phenotype tags used by Rule Cards and profiles (free strings, kept in one place).
STRICTURING = "stricturing"
LACTOSE_INTOLERANT = "lactose_intolerant"
IBS_LIKE_SYMPTOMS = "ibs_like_symptoms"
KNOWN_PHENOTYPES = frozenset({STRICTURING, LACTOSE_INTOLERANT, IBS_LIKE_SYMPTOMS})
