"""The nightly diary (spec 003): request / response models and the rules that turn answers
into the clinical index, sleep facts and red flags."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from happygut_engine import DiaryItems, Diagnosis, check_red_flags, index_for, is_late_night, sleep_hours

TimeOfDay = Literal["morning", "noon", "afternoon", "evening", "night"]
Reaction = Literal["stomach_ache", "bloating", "urgency", "nausea"]
PeriodType = Literal["exam", "work", "family", "fasting", "travel", "menstruation", "other"]
CLOCK = r"^([01]\d|2[0-3]):[0-5]\d$"


class DiaryFood(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12], max_length=40)
    name: str = Field(min_length=1, max_length=80)
    name_bn: str | None = Field(default=None, max_length=80)
    dish_id: str | None = Field(default=None, max_length=80)
    time_of_day: TimeOfDay = "noon"
    source: Literal["meal_check", "diary"] = "diary"
    meal_check_id: str | None = None
    reactions: list[Reaction] = Field(default_factory=list, max_length=4)


class Stool(BaseModel):
    count: int = Field(default=1, ge=0, le=30)
    night_count: int = Field(default=0, ge=0, le=30)
    bristol: int | None = Field(default=None, ge=1, le=7)
    blood: Literal["none", "streaks", "a_lot"] = "none"
    mucus: bool = False
    urgency: Literal["none", "hurry", "immediately", "incontinence"] = "none"


class Sleep(BaseModel):
    bedtime: str | None = Field(default=None, pattern=CLOCK)
    wake_time: str | None = Field(default=None, pattern=CLOCK)
    quality: Literal["good", "ok", "poor"] | None = None


class WarningSigns(BaseModel):
    fever: bool = False
    vomiting: bool = False
    no_stool_or_gas: bool = False
    dizzy_or_little_urine: bool = False


class DiaryIn(BaseModel):
    foods: list[DiaryFood] = Field(default_factory=list, max_length=40)
    stool: Stool = Field(default_factory=Stool)
    pain: int = Field(default=0, ge=0, le=3)
    wellbeing: int = Field(default=0, ge=0, le=4)
    medication: Literal["taken", "missed", "na"] = "na"
    notes: str = Field(default="", max_length=500)
    sleep: Sleep = Field(default_factory=Sleep)
    stress: int | None = Field(default=None, ge=0, le=4)
    signs: WarningSigns = Field(default_factory=WarningSigns)


class IndexOut(BaseModel):
    name: str
    score: int
    parts: dict[str, int]


class DiaryEntry(DiaryIn):
    """A stored diary day, with everything computed from the answers."""

    day: date
    completed_at: datetime
    completed_late: bool = False
    index: IndexOut
    sleep_hours: float | None = None
    late_night: bool | None = None
    red_flags: list[str] = Field(default_factory=list)
    is_synthetic: bool = False


class StressPeriodIn(BaseModel):
    type: PeriodType
    name: str = Field(min_length=1, max_length=60)
    start: date
    end: date


class StressPeriodOut(StressPeriodIn):
    id: str


def items_of(entry: DiaryIn) -> DiaryItems:
    stool = entry.stool
    return DiaryItems(
        stools=stool.count, night_stools=min(stool.night_count, stool.count), bristol=stool.bristol,
        blood=stool.blood, urgency=stool.urgency, pain=entry.pain, wellbeing=entry.wellbeing,
    )


def diary_red_flags(entry: DiaryIn) -> list[str]:
    """Structured answers first, then the same text sentinel as the meal check on the notes."""
    flags: list[str] = []
    if entry.stool.blood == "a_lot":
        flags.append("heavy_bleeding")
    if entry.signs.fever and entry.pain >= 1:
        flags.append("fever_with_abdominal_pain")
    if entry.signs.no_stool_or_gas and (entry.signs.vomiting or entry.pain >= 2):
        flags.append("possible_obstruction")
    if entry.signs.dizzy_or_little_urine:
        flags.append("severe_dehydration")
    for category in check_red_flags(entry.notes).categories:
        if category not in flags:
            flags.append(category)
    return flags


def build_entry(
    data: DiaryIn, day: date, diagnosis: Diagnosis, now: datetime, today: date,
    previous_bedtimes: list[str], is_synthetic: bool, scrubbed_notes: str,
) -> DiaryEntry:
    score = index_for(diagnosis, items_of(data))
    hours = late = None
    if data.sleep.bedtime:
        late = is_late_night(data.sleep.bedtime, previous_bedtimes)
        if data.sleep.wake_time:
            hours = sleep_hours(data.sleep.bedtime, data.sleep.wake_time)
    payload = data.model_dump()
    payload["notes"] = scrubbed_notes
    return DiaryEntry(
        **payload, day=day, completed_at=now, completed_late=day < today,
        index=IndexOut(name=score.name, score=score.score, parts=score.parts),
        sleep_hours=hours, late_night=late, red_flags=diary_red_flags(data), is_synthetic=is_synthetic,
    )
