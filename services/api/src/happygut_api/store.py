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

from happygut_engine import Component, Diagnosis, DiseaseState, PersonalEvidence, Profile


@dataclass(frozen=True)
class Patient:
    id: str
    diagnosis: Diagnosis
    state: DiseaseState
    phenotypes: frozenset[str]
    language: str
    is_synthetic: bool = False

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
    async def personal_evidence(self, patient_id: str) -> dict[Component, PersonalEvidence]: ...
    async def save_meal_check(self, record: MealCheckRecord) -> None: ...
    async def get_meal_check(self, patient_id: str, meal_check_id: str) -> MealCheckRecord | None: ...
    async def save_feedback(self, patient_id: str, meal_check_id: str, answer: str) -> bool: ...
    async def save_red_flag(self, patient_id: str, categories: list[str]) -> None: ...


class MemoryStore:
    """For tests and local demos."""

    def __init__(self):
        self.patients: dict[str, Patient] = {}  # by user id
        self.personal: dict[str, dict[Component, PersonalEvidence]] = {}
        self.meal_checks: dict[str, MealCheckRecord] = {}
        self.feedback: list[tuple[str, str, str]] = []
        self.red_flags: list[tuple[str, list[str]]] = []

    async def patient_for_user(self, user_id: str) -> Patient | None:
        return self.patients.get(user_id)

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
