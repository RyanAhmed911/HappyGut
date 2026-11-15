"""Patient-reported clinical indices from the nightly diary (spec 003 FR-005).

- HBI (Harvey-Bradshaw Index) for Crohn's disease
- SCCAI (Simple Clinical Colitis Activity Index) for ulcerative colitis

Only patient-reported items are scored. Items that need a clinician (abdominal mass in
the HBI) and complications / extracolonic features are scored 0, and the app says so.
The indices are for self-tracking, not diagnosis.
"""

from __future__ import annotations

from dataclasses import dataclass

from .vocab import Diagnosis

URGENCY = {"none": 0, "hurry": 1, "immediately": 2, "incontinence": 3}
BLOOD = {"none": 0, "streaks": 1, "a_lot": 3}


@dataclass(frozen=True)
class DiaryItems:
    """The diary answers the indices need."""

    stools: int = 0  # total stools today
    night_stools: int = 0  # of which at night
    bristol: int | None = None  # typical Bristol stool type 1-7
    blood: str = "none"  # none | streaks | a_lot
    urgency: str = "none"  # none | hurry | immediately | incontinence
    pain: int = 0  # 0 none · 1 mild · 2 moderate · 3 severe
    wellbeing: int = 0  # 0 very well · 1 slightly below par · 2 poor · 3 very poor · 4 terrible

    def __post_init__(self) -> None:
        if self.stools < 0 or self.night_stools < 0 or self.night_stools > self.stools:
            raise ValueError("stool counts must satisfy 0 <= night_stools <= stools")
        if self.bristol is not None and not 1 <= self.bristol <= 7:
            raise ValueError("bristol must be 1-7")
        if self.blood not in BLOOD or self.urgency not in URGENCY:
            raise ValueError("unknown blood or urgency value")
        if not 0 <= self.pain <= 3 or not 0 <= self.wellbeing <= 4:
            raise ValueError("pain must be 0-3 and wellbeing 0-4")


@dataclass(frozen=True)
class IndexScore:
    name: str  # HBI | SCCAI
    score: int
    parts: dict[str, int]


@dataclass(frozen=True)
class IndexThresholds:
    """Published activity cut-offs used to propose periods (spec 003 FR-021)."""

    active_at: int  # score >= this counts as an active day
    remission_below: int  # score < this counts as a calm day


THRESHOLDS = {
    "HBI": IndexThresholds(active_at=5, remission_below=5),
    "SCCAI": IndexThresholds(active_at=5, remission_below=3),  # remission is SCCAI <= 2
}


def hbi(items: DiaryItems) -> IndexScore:
    # "Number of liquid or soft stools per day": counted when the typical stool is Bristol 5-7.
    liquid = items.stools if items.bristol is not None and items.bristol >= 5 else 0
    parts = {"wellbeing": items.wellbeing, "abdominal_pain": items.pain, "liquid_stools": liquid,
             "abdominal_mass": 0, "complications": 0}
    return IndexScore("HBI", sum(parts.values()), parts)


def _bucket(value: int, edges: tuple[int, ...]) -> int:
    return sum(1 for edge in edges if value >= edge)


def sccai(items: DiaryItems) -> IndexScore:
    day = items.stools - items.night_stools
    parts = {
        "bowel_frequency_day": _bucket(day, (4, 7, 10)),  # 1-3: 0 · 4-6: 1 · 7-9: 2 · >9: 3
        "bowel_frequency_night": _bucket(items.night_stools, (1, 4)),  # 0: 0 · 1-3: 1 · 4-6: 2
        "urgency": URGENCY[items.urgency],
        "blood": BLOOD[items.blood],
        "wellbeing": items.wellbeing,
        "extracolonic": 0,
    }
    return IndexScore("SCCAI", sum(parts.values()), parts)


def index_for(diagnosis: Diagnosis, items: DiaryItems) -> IndexScore:
    return hbi(items) if diagnosis == Diagnosis.CD else sccai(items)


def index_name(diagnosis: Diagnosis) -> str:
    return "HBI" if diagnosis == Diagnosis.CD else "SCCAI"
