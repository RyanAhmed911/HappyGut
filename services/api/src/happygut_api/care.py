"""Medicines and tests: the patient's own schedule, for reminders and dose logging only.

Constitution II: HappyGut never suggests starting, stopping or changing a medicine. Everything
here is what the patient entered themselves; the app only reminds and records. There is no drug
database, no dose advice and no advice about missed doses (the app says to ask the doctor or
pharmacist instead).
"""

from __future__ import annotations

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

HHMM = r"^([01]\d|2[0-3]):[0-5]\d$"
EVERY_DAYS = (1, 7, 14, 21, 28, 42, 56)  # daily, weekly, every 2 / 3 / 4 / 6 / 8 weeks (injections, infusions)
MAX_MEDICATIONS = 12
MAX_APPOINTMENTS = 50
APPOINTMENT_KINDS = ("blood_test", "stool_test", "colonoscopy", "imaging", "doctor_visit", "other")


class MedicationIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    times: list[str] = Field(min_length=1, max_length=4)
    every_days: int = 1
    start: date
    note: str = Field(default="", max_length=80)

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name is empty")
        return v.strip()

    @field_validator("note")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @field_validator("times")
    @classmethod
    def _times(cls, v: list[str]) -> list[str]:
        if any(not re.match(HHMM, t) for t in v):
            raise ValueError("times must be HH:MM")
        return sorted(set(v))

    @field_validator("every_days")
    @classmethod
    def _every(cls, v: int) -> int:
        if v not in EVERY_DAYS:
            raise ValueError(f"every_days must be one of {EVERY_DAYS}")
        return v


class MedicationOut(MedicationIn):
    id: str


class AppointmentIn(BaseModel):
    kind: Literal["blood_test", "stool_test", "colonoscopy", "imaging", "doctor_visit", "other"]
    date: date
    time: str | None = Field(default=None, pattern=HHMM)
    note: str = Field(default="", max_length=80)

    @field_validator("note")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class AppointmentOut(AppointmentIn):
    id: str


class DoseIn(BaseModel):
    medication_id: str = Field(min_length=1, max_length=40)
    time: str = Field(pattern=HHMM)
    taken: bool


def is_due_on(med: MedicationIn, day: date) -> bool:
    """A medicine is due on its start date and every ``every_days`` after it."""
    return day >= med.start and (day - med.start).days % med.every_days == 0


def doses_for(meds: list[MedicationOut], day: date, taken: set[tuple[str, str]]) -> list[dict]:
    """Every dose due on ``day``, in time order, with whether the patient marked it taken."""
    doses = [
        {"medication_id": m.id, "name": m.name, "note": m.note, "time": t, "taken": (m.id, t) in taken}
        for m in meds if is_due_on(m, day) for t in m.times
    ]
    return sorted(doses, key=lambda d: (d["time"], d["name"]))
