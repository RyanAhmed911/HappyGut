"""Patient profiles, meal checks, feedback and red-flag events.

``PostgresStore`` talks to Supabase Postgres through the session pooler as the backend
(service) user: the ``core`` and ``events`` schemas are not exposed through the Data API.
Every query is scoped by patient ID, which comes from the verified JWT.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol

from datetime import date

from happygut_engine import Component, Diagnosis, DiseaseState, ManualFlare, PersonalEvidence, Profile

from .care import AppointmentOut, MedicationOut
from .diary import DiaryEntry, StressPeriodOut


class NotSupported(Exception):
    """This storage backend doesn't hold this data yet (the API answers 501)."""


@dataclass
class PeriodDecisions:
    confirmed: set[date] = field(default_factory=set)  # start dates of flares the user confirmed
    rejected: set[date] = field(default_factory=set)
    manual: list[ManualFlare] = field(default_factory=list)


@dataclass(frozen=True)
class Patient:
    id: str
    diagnosis: Diagnosis
    state: DiseaseState
    phenotypes: frozenset[str]
    language: str
    is_synthetic: bool = False
    display_name: str = ""
    reminder_time: str = "22:30"

    @property
    def profile(self) -> Profile:
        return Profile(diagnosis=self.diagnosis, state=self.state, phenotypes=self.phenotypes)


@dataclass
class MealCheckRecord:
    patient_id: str
    input_type: str  # photo | text
    input_text: str | None  # scrubbed
    dishes: list[dict]
    verdict: str
    risk: float
    confidence: float
    evidence_ids: list[str]
    explanation: dict
    engine_version: str
    model_versions: dict
    prompt_versions: dict
    is_synthetic: bool
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def public(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "input_type": self.input_type,
            "dishes": self.dishes,
            "verdict": self.verdict,
            "risk": self.risk,
            "confidence": self.confidence,
            "evidence_ids": self.evidence_ids,
            "explanation": self.explanation,
            "engine_version": self.engine_version,
            "is_synthetic": self.is_synthetic,
        }


class Store(Protocol):
    async def patient_for_user(self, user_id: str) -> Patient | None: ...
    async def all_patients(self) -> list[Patient]: ...
    async def personal_evidence(self, patient_id: str) -> dict[Component, PersonalEvidence]: ...
    async def save_meal_check(self, record: MealCheckRecord) -> None: ...
    async def get_meal_check(self, patient_id: str, meal_check_id: str) -> MealCheckRecord | None: ...
    async def save_feedback(self, patient_id: str, meal_check_id: str, answer: str) -> bool: ...
    async def save_red_flag(self, patient_id: str, categories: list[str]) -> None: ...
    # Spec 003: diary, stressful periods, period decisions
    async def update_patient(self, patient_id: str, language: str | None, reminder_time: str | None,
                             diagnosis: Diagnosis | None = None, phenotypes: frozenset[str] | None = None) -> Patient | None: ...
    async def list_meal_checks(self, patient_id: str, limit: int = 30) -> list[MealCheckRecord]: ...
    async def save_diary(self, patient_id: str, entry: DiaryEntry) -> None: ...
    async def get_diary(self, patient_id: str, day: date) -> DiaryEntry | None: ...
    async def list_diary(self, patient_id: str) -> list[DiaryEntry]: ...
    async def list_stress_periods(self, patient_id: str) -> list[StressPeriodOut]: ...
    async def add_stress_period(self, patient_id: str, period: StressPeriodOut) -> None: ...
    async def delete_stress_period(self, patient_id: str, period_id: str) -> bool: ...
    async def period_decisions(self, patient_id: str) -> PeriodDecisions: ...
    async def save_period_decisions(self, patient_id: str, decisions: PeriodDecisions) -> None: ...
    async def data_version(self, patient_id: str) -> int: ...
    async def list_weights(self, patient_id: str) -> list[tuple[date, float]]: ...
    async def save_weight(self, patient_id: str, day: date, kg: float) -> None: ...
    async def delete_weight(self, patient_id: str, day: date) -> bool: ...
    async def list_medications(self, patient_id: str) -> list[MedicationOut]: ...
    async def save_medication(self, patient_id: str, med: MedicationOut) -> None: ...
    async def delete_medication(self, patient_id: str, medication_id: str) -> bool: ...
    async def doses_taken(self, patient_id: str, day: date) -> set[tuple[str, str]]: ...
    async def set_dose(self, patient_id: str, day: date, medication_id: str, time: str, taken: bool) -> None: ...
    async def list_appointments(self, patient_id: str) -> list[AppointmentOut]: ...
    async def add_appointment(self, patient_id: str, appointment: AppointmentOut) -> None: ...
    async def delete_appointment(self, patient_id: str, appointment_id: str) -> bool: ...


class MemoryStore:
    """For tests and local demos."""

    def __init__(self):
        self.patients: dict[str, Patient] = {}  # by user id
        self.personal: dict[str, dict[Component, PersonalEvidence]] = {}
        self.meal_checks: dict[str, MealCheckRecord] = {}
        self.feedback: list[tuple[str, str, str]] = []
        self.red_flags: list[tuple[str, list[str]]] = []
        self.diary: dict[str, dict[date, DiaryEntry]] = {}
        self.stress_periods: dict[str, list[StressPeriodOut]] = {}
        self.decisions: dict[str, PeriodDecisions] = {}
        self.weights: dict[str, dict[date, float]] = {}
        self.medications: dict[str, dict[str, MedicationOut]] = {}  # patient → id → medicine (insertion order kept)
        self.doses: dict[str, dict[date, set[tuple[str, str]]]] = {}  # patient → day → {(medicine id, time)} taken
        self.appointments: dict[str, list[AppointmentOut]] = {}
        self.versions: dict[str, int] = {}

    def _bump(self, patient_id: str) -> None:
        self.versions[patient_id] = self.versions.get(patient_id, 0) + 1

    def clear_patient(self, patient_id: str) -> None:
        """Forget everything stored for one patient (used to restore a test account's sample records)."""
        for user_id in [u for u, p in self.patients.items() if p.id == patient_id]:
            del self.patients[user_id]
        for table in (self.personal, self.diary, self.stress_periods, self.decisions, self.weights, self.medications,
                      self.doses, self.appointments):
            table.pop(patient_id, None)
        self.meal_checks = {k: r for k, r in self.meal_checks.items() if r.patient_id != patient_id}
        self.feedback = [f for f in self.feedback if f[0] != patient_id]
        self.red_flags = [f for f in self.red_flags if f[0] != patient_id]
        self._bump(patient_id)  # never reuse a version number: caches keyed on it must miss

    async def patient_for_user(self, user_id: str) -> Patient | None:
        return self.patients.get(user_id)

    async def all_patients(self) -> list[Patient]:
        return list(self.patients.values())

    async def personal_evidence(self, patient_id: str) -> dict[Component, PersonalEvidence]:
        return self.personal.get(patient_id, {})

    async def save_meal_check(self, record: MealCheckRecord) -> None:
        self.meal_checks[record.id] = record

    async def get_meal_check(self, patient_id: str, meal_check_id: str) -> MealCheckRecord | None:
        r = self.meal_checks.get(meal_check_id)
        return r if r is not None and r.patient_id == patient_id else None

    async def save_feedback(self, patient_id: str, meal_check_id: str, answer: str) -> bool:
        if await self.get_meal_check(patient_id, meal_check_id) is None:
            return False
        self.feedback.append((patient_id, meal_check_id, answer))
        return True

    async def save_red_flag(self, patient_id: str, categories: list[str]) -> None:
        self.red_flags.append((patient_id, categories))

    async def update_patient(self, patient_id: str, language: str | None, reminder_time: str | None,
                             diagnosis: Diagnosis | None = None, phenotypes: frozenset[str] | None = None) -> Patient | None:
        from dataclasses import replace

        for user_id, p in self.patients.items():
            if p.id == patient_id:
                self.patients[user_id] = replace(
                    p, language=language or p.language, reminder_time=reminder_time or p.reminder_time,
                    diagnosis=diagnosis or p.diagnosis, phenotypes=p.phenotypes if phenotypes is None else phenotypes)
                self._bump(patient_id)
                return self.patients[user_id]
        return None

    async def list_meal_checks(self, patient_id: str, limit: int = 30) -> list[MealCheckRecord]:
        mine = [r for r in self.meal_checks.values() if r.patient_id == patient_id]
        return sorted(mine, key=lambda r: r.created_at, reverse=True)[:limit]

    async def save_diary(self, patient_id: str, entry: DiaryEntry) -> None:
        self.diary.setdefault(patient_id, {})[entry.day] = entry
        self._bump(patient_id)

    async def get_diary(self, patient_id: str, day: date) -> DiaryEntry | None:
        return self.diary.get(patient_id, {}).get(day)

    async def list_diary(self, patient_id: str) -> list[DiaryEntry]:
        return [e for _, e in sorted(self.diary.get(patient_id, {}).items())]

    async def list_stress_periods(self, patient_id: str) -> list[StressPeriodOut]:
        return sorted(self.stress_periods.get(patient_id, []), key=lambda p: p.start)

    async def add_stress_period(self, patient_id: str, period: StressPeriodOut) -> None:
        self.stress_periods.setdefault(patient_id, []).append(period)
        self._bump(patient_id)

    async def delete_stress_period(self, patient_id: str, period_id: str) -> bool:
        periods = self.stress_periods.get(patient_id, [])
        kept = [p for p in periods if p.id != period_id]
        self.stress_periods[patient_id] = kept
        self._bump(patient_id)
        return len(kept) != len(periods)

    async def period_decisions(self, patient_id: str) -> PeriodDecisions:
        return self.decisions.setdefault(patient_id, PeriodDecisions())

    async def save_period_decisions(self, patient_id: str, decisions: PeriodDecisions) -> None:
        self.decisions[patient_id] = decisions
        self._bump(patient_id)

    async def data_version(self, patient_id: str) -> int:
        return self.versions.get(patient_id, 0)

    async def list_weights(self, patient_id: str) -> list[tuple[date, float]]:
        return sorted(self.weights.get(patient_id, {}).items())

    async def save_weight(self, patient_id: str, day: date, kg: float) -> None:
        self.weights.setdefault(patient_id, {})[day] = kg  # one weigh-in per day; a second one replaces it

    async def delete_weight(self, patient_id: str, day: date) -> bool:
        return self.weights.get(patient_id, {}).pop(day, None) is not None

    async def list_medications(self, patient_id: str) -> list[MedicationOut]:
        return list(self.medications.get(patient_id, {}).values())

    async def save_medication(self, patient_id: str, med: MedicationOut) -> None:
        self.medications.setdefault(patient_id, {})[med.id] = med  # add, or replace when editing

    async def delete_medication(self, patient_id: str, medication_id: str) -> bool:
        return self.medications.get(patient_id, {}).pop(medication_id, None) is not None

    async def doses_taken(self, patient_id: str, day: date) -> set[tuple[str, str]]:
        return set(self.doses.get(patient_id, {}).get(day, set()))

    async def set_dose(self, patient_id: str, day: date, medication_id: str, time: str, taken: bool) -> None:
        marks = self.doses.setdefault(patient_id, {}).setdefault(day, set())
        if taken:
            marks.add((medication_id, time))
        else:
            marks.discard((medication_id, time))

    async def list_appointments(self, patient_id: str) -> list[AppointmentOut]:
        return sorted(self.appointments.get(patient_id, []), key=lambda a: (a.date, a.time or ""))

    async def add_appointment(self, patient_id: str, appointment: AppointmentOut) -> None:
        self.appointments.setdefault(patient_id, []).append(appointment)

    async def delete_appointment(self, patient_id: str, appointment_id: str) -> bool:
        items = self.appointments.get(patient_id, [])
        kept = [a for a in items if a.id != appointment_id]
        self.appointments[patient_id] = kept
        return len(kept) != len(items)


class PostgresStore:
    def __init__(self, dsn: str):
        self.dsn = dsn

    async def _conn(self):
        import psycopg

        # prepare_threshold=None: the Supabase pooler doesn't support prepared statements in transaction mode.
        return await psycopg.AsyncConnection.connect(self.dsn, autocommit=True, prepare_threshold=None)

    async def patient_for_user(self, user_id: str) -> Patient | None:
        async with await self._conn() as conn:
            cur = await conn.execute(
                "select id, diagnosis, state, phenotypes, language, is_synthetic from core.patients where user_id = %s",
                (user_id,),
            )
            row = await cur.fetchone()
        if row is None:
            return None
        return Patient(str(row[0]), Diagnosis(row[1]), DiseaseState(row[2]), frozenset(row[3] or ()), row[4], bool(row[5]))

    async def personal_evidence(self, patient_id: str) -> dict[Component, PersonalEvidence]:
        # The Personal Gut Graph is built in spec 003; until then there is no learned evidence.
        return {}

    async def save_meal_check(self, r: MealCheckRecord) -> None:
        async with await self._conn() as conn:
            await conn.execute(
                """insert into events.meal_checks
                   (id, patient_id, created_at, input_type, input_text, dishes, verdict, risk, confidence,
                    evidence_ids, explanation, engine_version, model_versions, prompt_versions, is_synthetic)
                   values (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s::jsonb, %s, %s::jsonb, %s::jsonb, %s)""",
                (r.id, r.patient_id, r.created_at, r.input_type, r.input_text, json.dumps(r.dishes, ensure_ascii=False),
                 r.verdict, r.risk, r.confidence, r.evidence_ids, json.dumps(r.explanation, ensure_ascii=False),
                 r.engine_version, json.dumps(r.model_versions), json.dumps(r.prompt_versions), r.is_synthetic),
            )

    async def get_meal_check(self, patient_id: str, meal_check_id: str) -> MealCheckRecord | None:
        async with await self._conn() as conn:
            cur = await conn.execute(
                """select id, created_at, input_type, input_text, dishes, verdict, risk, confidence, evidence_ids,
                          explanation, engine_version, model_versions, prompt_versions, is_synthetic
                   from events.meal_checks where id = %s and patient_id = %s""",
                (meal_check_id, patient_id),
            )
            row = await cur.fetchone()
        if row is None:
            return None
        return MealCheckRecord(
            patient_id=patient_id, input_type=row[2], input_text=row[3], dishes=row[4], verdict=row[5],
            risk=float(row[6] or 0), confidence=float(row[7] or 0), evidence_ids=list(row[8]), explanation=row[9] or {},
            engine_version=row[10], model_versions=row[11], prompt_versions=row[12], is_synthetic=row[13],
            id=str(row[0]), created_at=row[1],
        )

    async def save_feedback(self, patient_id: str, meal_check_id: str, answer: str) -> bool:
        async with await self._conn() as conn:
            cur = await conn.execute(
                """insert into events.verdict_feedback (meal_check_id, meal_check_created_at, patient_id, answer)
                   select id, created_at, patient_id, %s from events.meal_checks where id = %s and patient_id = %s""",
                (answer, meal_check_id, patient_id),
            )
            return cur.rowcount == 1

    async def save_red_flag(self, patient_id: str, categories: list[str]) -> None:
        async with await self._conn() as conn:
            await conn.execute(
                "insert into events.red_flag_events (patient_id, categories) values (%s, %s)", (patient_id, categories)
            )

    # Spec 003 storage (diary, stressful periods, period decisions) needs a migration that isn't
    # written yet. Until then these features run on the in-memory store (demo mode).
    async def update_patient(self, patient_id: str, language: str | None, reminder_time: str | None,
                             diagnosis: Diagnosis | None = None, phenotypes: frozenset[str] | None = None) -> Patient | None:
        async with await self._conn() as conn:
            if language:
                await conn.execute("update core.patients set language = %s where id = %s", (language, patient_id))
            if diagnosis:
                await conn.execute("update core.patients set diagnosis = %s where id = %s", (diagnosis.value, patient_id))
            if phenotypes is not None:
                await conn.execute("update core.patients set phenotypes = %s where id = %s", (sorted(phenotypes), patient_id))
            cur = await conn.execute(
                "select id, diagnosis, state, phenotypes, language, is_synthetic from core.patients where id = %s", (patient_id,))
            row = await cur.fetchone()
        if row is None:
            return None
        return Patient(str(row[0]), Diagnosis(row[1]), DiseaseState(row[2]), frozenset(row[3] or ()), row[4], bool(row[5]),
                       reminder_time=reminder_time or "22:30")

    async def list_meal_checks(self, patient_id: str, limit: int = 30) -> list[MealCheckRecord]:
        async with await self._conn() as conn:
            cur = await conn.execute(
                "select id from events.meal_checks where patient_id = %s order by created_at desc limit %s", (patient_id, limit))
            ids = [str(r[0]) for r in await cur.fetchall()]
        return [r for r in [await self.get_meal_check(patient_id, i) for i in ids] if r is not None]

    async def save_diary(self, patient_id: str, entry: DiaryEntry) -> None:
        raise NotSupported("diary")

    async def get_diary(self, patient_id: str, day: date) -> DiaryEntry | None:
        raise NotSupported("diary")

    async def list_diary(self, patient_id: str) -> list[DiaryEntry]:
        raise NotSupported("diary")

    async def list_stress_periods(self, patient_id: str) -> list[StressPeriodOut]:
        raise NotSupported("stress_periods")

    async def add_stress_period(self, patient_id: str, period: StressPeriodOut) -> None:
        raise NotSupported("stress_periods")

    async def delete_stress_period(self, patient_id: str, period_id: str) -> bool:
        raise NotSupported("stress_periods")

    async def period_decisions(self, patient_id: str) -> PeriodDecisions:
        raise NotSupported("periods")

    async def save_period_decisions(self, patient_id: str, decisions: PeriodDecisions) -> None:
        raise NotSupported("periods")

    async def data_version(self, patient_id: str) -> int:
        return 0

    async def all_patients(self) -> list[Patient]:
        raise NotSupported("jobs")

    async def list_weights(self, patient_id: str) -> list[tuple[date, float]]:
        raise NotSupported("weights")

    async def save_weight(self, patient_id: str, day: date, kg: float) -> None:
        raise NotSupported("weights")

    async def delete_weight(self, patient_id: str, day: date) -> bool:
        raise NotSupported("weights")

    async def list_medications(self, patient_id: str) -> list[MedicationOut]:
        raise NotSupported("medications")

    async def save_medication(self, patient_id: str, med: MedicationOut) -> None:
        raise NotSupported("medications")

    async def delete_medication(self, patient_id: str, medication_id: str) -> bool:
        raise NotSupported("medications")

    async def doses_taken(self, patient_id: str, day: date) -> set[tuple[str, str]]:
        raise NotSupported("medications")

    async def set_dose(self, patient_id: str, day: date, medication_id: str, time: str, taken: bool) -> None:
        raise NotSupported("medications")

    async def list_appointments(self, patient_id: str) -> list[AppointmentOut]:
        raise NotSupported("appointments")

    async def add_appointment(self, patient_id: str, appointment: AppointmentOut) -> None:
        raise NotSupported("appointments")

    async def delete_appointment(self, patient_id: str, appointment_id: str) -> bool:
        raise NotSupported("appointments")
