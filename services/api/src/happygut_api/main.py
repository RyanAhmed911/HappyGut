"""FastAPI app: /v1 REST API. The meal check streams (SSE over POST); the rest is JSON."""

from __future__ import annotations

import json
import logging
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, replace
from datetime import date, datetime
from typing import AsyncIterator, Literal

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from happygut_engine import DEFAULT_CONFIG, Diagnosis, ManualFlare, index_for, usual_bedtime

from . import __version__, foods, i18n
from .agents import PydanticExplainer, PydanticPerceiver, Unavailable, build_model
from .auth import AuthError, SupabaseVerifier, Verifier
from .demo import PERSONAS, DemoVerifier, TestAccounts, seed_demo, seed_persona
from .diary import CLOCK, DiaryIn, IndexOut, StressPeriodIn, StressPeriodOut, build_entry, items_of
from .flow import Event, MealCheckFlow
from .images import ImageRejected, sanitise
from .insights import SCOPES, Insights
from .knowledge import Knowledge, MemoryKnowledge
from .model_catalog import choose
from .pii import Scrubber, build_scrubber
from .prompts import load_prompt
from .settings import Settings, get_settings
from .store import MemoryStore, NotSupported, Patient, PostgresStore, Store

log = logging.getLogger("happygut.api")
MAX_TEXT = 1000
DIARY_EDIT_DAYS = 2  # a diary can be filled in up to 2 days late (spec 003 FR-007)
Lang = Literal["bn", "en"]


class Feedback(BaseModel):
    answer: Literal["right", "wrong", "not_sure"]


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=1, max_length=200)


class ProfileUpdate(BaseModel):
    language: Lang | None = None
    reminder_time: str | None = Field(default=None, pattern=CLOCK)
    diagnosis: Literal["CD", "UC"] | None = None
    phenotypes: list[Literal["stricturing", "lactose_intolerant", "ibs_like_symptoms"]] | None = Field(default=None, max_length=3)


class PeriodDecision(BaseModel):
    start: date
    decision: Literal["confirm", "reject"]


class ManualFlareIn(BaseModel):
    start: date
    end: date | None = None


@dataclass
class Services:
    settings: Settings
    knowledge: Knowledge
    store: Store
    verifier: Verifier
    flow: MealCheckFlow
    insights: Insights | None = None
    scrubber: Scrubber | None = None
    demo: DemoVerifier | None = None
    accounts: TestAccounts | None = None
    models: dict[str, bool] | None = None
    model_names: dict[str, list[str]] | None = None

    def __post_init__(self) -> None:
        self.insights = self.insights or Insights(self.store, self.knowledge, self.settings.timezone)
        self.scrubber = self.scrubber or self.flow.scrubber
        if self.flow.personal is None:
            self.flow.personal = self.insights.personal_evidence


def build_services(settings: Settings) -> Services:
    knowledge = MemoryKnowledge.from_seeds(settings.seeds_dir, include_drafts=settings.include_draft_seeds)
    demo = DemoVerifier(settings.session_secret) if settings.demo_mode else None
    accounts = TestAccounts({"nusrat": settings.test_password_nusrat, "rafi": settings.test_password_rafi,
                             "ayesha": settings.test_password_ayesha}) if settings.demo_mode else None
    store: Store = MemoryStore() if settings.demo_mode or not settings.supabase_db_url else PostgresStore(settings.supabase_db_url)
    models = {"perception": True, "explanation": True}
    if settings.resolve_models and (settings.gemini_api_key or settings.groq_api_key):
        choice = choose(settings)
        perception_names, explanation_names = choice.perception, choice.explanation
    else:
        perception_names = [settings.perception_model, settings.perception_fallback_model]
        explanation_names = [settings.explanation_model, settings.explanation_fallback_model]
    log.info("models: perception %s, explanation %s", perception_names, explanation_names)
    try:
        perceiver = PydanticPerceiver(
            build_model(perception_names, settings.gemini_api_key, settings.groq_api_key, settings.gemini_base_url),
            load_prompt(settings.prompts_dir, "meal-perception"), settings.model_timeout_s)
    except RuntimeError:
        log.warning("no perception model key: photos are unavailable, typed text still works")
        perceiver, models["perception"] = Unavailable(), False
    try:
        explainer = PydanticExplainer(
            build_model(explanation_names, settings.gemini_api_key, settings.groq_api_key, settings.gemini_base_url),
            load_prompt(settings.prompts_dir, "meal-explanation"), settings.model_timeout_s)
    except RuntimeError:
        log.warning("no explanation model key: explanations use the cited template")
        explainer, models["explanation"] = Unavailable(), False
    scrubber = build_scrubber(settings.pii_presidio, settings.pii_bengali_ner_model, knowledge.all_names())
    flow = MealCheckFlow(knowledge, perceiver, explainer, scrubber, store)
    verifier: Verifier = demo if demo else SupabaseVerifier(settings.supabase_url, settings.jwt_audience)
    names = {"perception": perception_names if models["perception"] else [],
             "explanation": explanation_names if models["explanation"] else []}
    return Services(settings, knowledge, store, verifier, flow, demo=demo, accounts=accounts, models=models, model_names=names)


def create_app(services: Services | None = None) -> FastAPI:
    holder: dict[str, Services] = {}

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        s = holder["s"] = services or build_services(get_settings())
        log.info("knowledge loaded: %s (reviewed only: %s)", s.knowledge.counts(), s.knowledge.reviewed_only)
        if s.demo is not None and isinstance(s.store, MemoryStore) and isinstance(s.knowledge, MemoryKnowledge):
            await seed_demo(s.store, s.knowledge, s.insights, s.flow)
            log.info("test accounts ready: %s", ", ".join(p.email for p in PERSONAS))
            for email, password in (s.accounts.generated if s.accounts else {}).items():
                # Only generated, per-run passwords are printed; configured ones never are.
                print(f"  test account {email}: no password configured, using {password} for this run", flush=True)
        yield

    settings = services.settings if services else get_settings()
    app = FastAPI(title="HappyGut API", version=__version__, lifespan=lifespan,
                  description="Self-management support, not a medical device. Verdicts come from the HappyGut engine.")
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
                       allow_headers=["Authorization", "Content-Type"])

    @app.exception_handler(NotSupported)
    async def not_supported(_: Request, exc: NotSupported) -> JSONResponse:
        return JSONResponse({"detail": f"not_available_on_this_storage:{exc}"}, status_code=501)

    def svc() -> Services:
        return holder["s"]

    async def current_patient(authorization: str = Header(default=""), s: Services = Depends(svc)) -> Patient:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(401, "missing_token")
        try:
            user_id = s.verifier.user_id(token)
        except AuthError:
            raise HTTPException(401, "invalid_token") from None
        patient = await s.store.patient_for_user(user_id)
        if patient is None:
            raise HTTPException(404, "no_profile")
        return patient

    async def profile(patient: Patient, s: Services) -> dict:
        try:
            state = (await s.insights.effective_state(patient)).value
        except NotSupported:
            state = patient.state.value
        return {
            "id": patient.id, "display_name": patient.display_name, "diagnosis": patient.diagnosis.value,
            "phenotypes": sorted(patient.phenotypes), "state": state, "language": patient.language,
            "reminder_time": patient.reminder_time, "is_synthetic": patient.is_synthetic,
        }

    # ------------------------------------------------------------ health, demo, profile

    @app.get("/v1/health")
    async def health(s: Services = Depends(svc)) -> dict:
        return {
            "status": "ok", "version": __version__, "engine_version": DEFAULT_CONFIG.version,
            "knowledge": {**s.knowledge.counts(), "reviewed_only": s.knowledge.reviewed_only},
            "storage": type(s.store).__name__, "demo_mode": s.demo is not None, "sign_in": s.accounts is not None,
            "models": s.models or {"perception": True, "explanation": True},
            "model_names": s.model_names or {},
        }

    @app.post("/v1/auth/login")
    async def login(body: Credentials, s: Services = Depends(svc)) -> dict:
        if s.demo is None or s.accounts is None:
            raise HTTPException(404, "sign_in_unavailable")
        if s.accounts.locked(body.email.strip().lower()):
            raise HTTPException(429, "too_many_attempts")
        persona = s.accounts.check(body.email, body.password)
        if persona is None:
            raise HTTPException(401, "invalid_credentials")
        return {"token": s.demo.issue(persona.user_id), "expires_in": 12 * 3600}

    @app.post("/v1/account/restore")
    async def restore_account(patient: Patient = Depends(current_patient), s: Services = Depends(svc)) -> dict:
        """Put a test account's sample records back as they were (any judge may have changed them)."""
        persona = next((p for p in PERSONAS if p.patient_id == patient.id), None)
        if persona is None or not isinstance(s.store, MemoryStore) or not isinstance(s.knowledge, MemoryKnowledge):
            raise HTTPException(404, "not_a_test_account")
        restored = await seed_persona(persona, s.store, s.knowledge, s.insights, s.flow)
        restored = await s.store.update_patient(restored.id, patient.language, None) or restored
        return await profile(restored, s)

    @app.get("/v1/me")
    async def me(patient: Patient = Depends(current_patient), s: Services = Depends(svc)) -> dict:
        return await profile(patient, s)

    @app.patch("/v1/me")
    async def update_me(body: ProfileUpdate, patient: Patient = Depends(current_patient), s: Services = Depends(svc)) -> dict:
        updated = await s.store.update_patient(
            patient.id, body.language, body.reminder_time,
            Diagnosis(body.diagnosis) if body.diagnosis else None,
            frozenset(body.phenotypes) if body.phenotypes is not None else None)
        updated = updated or patient
        if updated.diagnosis != patient.diagnosis:
            # The clinical index follows the diagnosis (HBI for Crohn's, SCCAI for UC): rescore the stored days.
            for entry in await s.store.list_diary(updated.id):
                score = index_for(updated.diagnosis, items_of(entry))
                entry.index = IndexOut(name=score.name, score=score.score, parts=score.parts)
                await s.store.save_diary(updated.id, entry)
        return await profile(updated, s)

    @app.get("/v1/foods/search")
    async def food_search(q: str = Query(min_length=1, max_length=80), _: Patient = Depends(current_patient),
                          s: Services = Depends(svc)) -> dict:
        graph = getattr(s.knowledge, "graph", None)
        matches = graph.search_dish(q, limit=6, threshold=0.35) if graph is not None else []
        return {"results": [{"dish_id": m.dish_id, "name_en": m.name_en, "name_bn": m.name_bn, "score": m.score} for m in matches]}

    async def food_guide(patient: Patient, s: Services) -> list[dict]:
        if not isinstance(s.knowledge, MemoryKnowledge):
            raise NotSupported("food_guide")
        try:
            state = await s.insights.effective_state(patient)
            personal = await s.insights.personal_evidence(patient)
        except NotSupported:
            state, personal = patient.state, {}
        return foods.guide(s.knowledge, replace(patient, state=state).profile, personal)

    @app.get("/v1/foods/guide")
    async def get_food_guide(patient: Patient = Depends(current_patient), s: Services = Depends(svc)) -> dict:
        return {"items": await food_guide(patient, s)}

    @app.get("/v1/foods/plan")
    async def get_meal_plan(patient: Patient = Depends(current_patient), s: Services = Depends(svc)) -> dict:
        today = s.insights.today()
        year, week, _ = today.isocalendar()
        seed = f"{patient.id}:{year}-{week}:{patient.diagnosis.value}:{sorted(patient.phenotypes)}"
        return {**foods.plan(await food_guide(patient, s), today, seed), "start": today.isoformat()}

    # ------------------------------------------------------------ meal checks

    @app.post("/v1/meal-checks")
    async def meal_check(
        text: str | None = Form(default=None),
        lang: Lang | None = Form(default=None),
        image: UploadFile | None = File(default=None),
        patient: Patient = Depends(current_patient),
        s: Services = Depends(svc),
    ) -> StreamingResponse:
        text = (text or "").strip() or None
        if text is None and image is None:
            raise HTTPException(422, "text_or_image_required")
        if text is not None and len(text) > MAX_TEXT:
            raise HTTPException(422, "text_too_long")
        clean = None
        if image is not None:
            raw = await image.read(s.settings.max_image_bytes + 1)
            try:
                clean = sanitise(raw, s.settings.max_image_bytes, s.settings.max_image_side)
            except ImageRejected as exc:
                raise HTTPException(413 if exc.code == "image_too_large" else 422, exc.code) from None
        try:
            patient = replace(patient, state=await s.insights.effective_state(patient))
        except NotSupported:
            pass
        return StreamingResponse(_sse(s.flow.stream(patient, lang or patient.language, text, clean)),
                                 media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.get("/v1/meal-checks")
    async def list_meal_checks(limit: int = Query(default=30, ge=1, le=100), patient: Patient = Depends(current_patient),
                               s: Services = Depends(svc)) -> dict:
        records = await s.store.list_meal_checks(patient.id, limit)
        return {"items": [r.public() for r in records]}

    @app.get("/v1/meal-checks/{meal_check_id}")
    async def get_meal_check(meal_check_id: uuid.UUID, patient: Patient = Depends(current_patient),
                             s: Services = Depends(svc)) -> dict:
        record = await s.store.get_meal_check(patient.id, str(meal_check_id))
        if record is None:
            raise HTTPException(404, "not_found")
        return record.public()

    @app.post("/v1/meal-checks/{meal_check_id}/feedback", status_code=201)
    async def feedback(meal_check_id: uuid.UUID, body: Feedback, patient: Patient = Depends(current_patient),
                       s: Services = Depends(svc)) -> dict:
        if not await s.store.save_feedback(patient.id, str(meal_check_id), body.answer):
            raise HTTPException(404, "not_found")
        return {"status": "saved"}

    # ------------------------------------------------------------ nightly diary

    def time_of_day(moment: datetime) -> str:
        hour = moment.hour
        return "morning" if hour < 11 else "noon" if hour < 15 else "afternoon" if hour < 18 else "evening" if hour < 22 else "night"

    async def prefill(patient: Patient, day: date, s: Services, existing_ids: set[str]) -> list[dict]:
        """Dishes from that day's meal checks that aren't in the diary yet (spec 003 FR-002)."""
        foods = []
        for record in await s.store.list_meal_checks(patient.id, 100):
            local = record.created_at.astimezone(s.insights.tz)
            if local.date() != day or record.id in existing_ids:
                continue
            for dish in record.dishes:
                en, bn = (s.knowledge.names(dish["dish_id"]) if dish.get("dish_id") else (dish["name"], None))
                foods.append({"name": en, "name_bn": bn, "dish_id": dish.get("dish_id"), "time_of_day": time_of_day(local),
                              "source": "meal_check", "meal_check_id": record.id, "reactions": []})
        return foods

    def check_day(day: date, s: Services) -> date:
        today = s.insights.today()
        if day > today:
            raise HTTPException(422, "future_date")
        return today

    @app.get("/v1/diary/days")
    async def diary_days(limit: int = Query(default=180, ge=1, le=366), patient: Patient = Depends(current_patient),
                         s: Services = Depends(svc)) -> dict:
        return {"days": await s.insights.days(patient, limit), "today": s.insights.today().isoformat(),
                "is_synthetic": patient.is_synthetic}

    @app.get("/v1/diary/{day}")
    async def get_diary(day: date, patient: Patient = Depends(current_patient), s: Services = Depends(svc)) -> dict:
        today = check_day(day, s)
        entry = await s.store.get_diary(patient.id, day)
        used = {f.meal_check_id for f in entry.foods if f.meal_check_id} if entry else set()
        recent = [e for e in await s.store.list_diary(patient.id) if e.day < day][-14:]
        scores = sorted(e.index.score for e in recent)
        bedtimes = [e.sleep.bedtime for e in recent if e.sleep.bedtime]
        return {
            "date": day.isoformat(), "today": today.isoformat(),
            "editable": (today - day).days <= DIARY_EDIT_DAYS,
            "entry": entry.model_dump(mode="json") if entry else None,
            "prefill": await prefill(patient, day, s, used),
            "usual": {"index": scores[len(scores) // 2] if scores else None,
                      "bedtime": usual_bedtime(bedtimes),
                      "medication": "taken" if any(e.medication != "na" for e in recent) else "na"},
            "tags": [p.model_dump(mode="json") for p in await s.store.list_stress_periods(patient.id) if p.start <= day <= p.end],
        }

    @app.put("/v1/diary/{day}")
    async def save_diary(day: date, body: DiaryIn, lang: Lang | None = None, patient: Patient = Depends(current_patient),
                         s: Services = Depends(svc)) -> dict:
        today = check_day(day, s)
        if (today - day).days > DIARY_EDIT_DAYS:
            raise HTTPException(422, "too_late_to_edit")
        language = lang or patient.language
        earlier = [e for e in await s.store.list_diary(patient.id) if e.day < day]
        bedtimes = [e.sleep.bedtime for e in earlier if e.sleep.bedtime]
        # Red flags are judged on the raw answers and notes; notes are stored scrubbed.
        entry = build_entry(body, day, patient.diagnosis, s.insights.now(), today, bedtimes, patient.is_synthetic,
                            s.scrubber.scrub(body.notes).text if body.notes else "")
        await s.store.save_diary(patient.id, entry)
        out: dict = {"entry": entry.model_dump(mode="json"), "red_flag": None, "comparison": None}
        if entry.red_flags:
            # Stop here: no diet or lifestyle feedback, escalate (spec 003 FR-006).
            await s.store.save_red_flag(patient.id, entry.red_flags)
            out["red_flag"] = {
                "categories": entry.red_flags, "title": i18n.t(language, "red_flag.title"),
                "message": i18n.t(language, "red_flag.body"),
                "reasons": [i18n.t(language, f"red_flag.category.{c}") for c in entry.red_flags],
            }
            return out
        recent = sorted(e.index.score for e in earlier[-14:])
        if len(recent) >= 3:
            usual = recent[len(recent) // 2]
            out["comparison"] = {"usual": usual, "delta": entry.index.score - usual, "days": len(recent)}
        return out

    # ------------------------------------------------------------ stressful periods

    @app.get("/v1/stress-periods")
    async def list_stress_periods(patient: Patient = Depends(current_patient), s: Services = Depends(svc)) -> dict:
        return {"items": [p.model_dump(mode="json") for p in await s.store.list_stress_periods(patient.id)]}

    @app.post("/v1/stress-periods", status_code=201)
    async def add_stress_period(body: StressPeriodIn, patient: Patient = Depends(current_patient),
                                s: Services = Depends(svc)) -> dict:
        if body.end < body.start or (body.end - body.start).days > 120:
            raise HTTPException(422, "bad_date_range")
        period = StressPeriodOut(id=uuid.uuid4().hex[:12], **body.model_dump())
        await s.store.add_stress_period(patient.id, period)
        return period.model_dump(mode="json")

    @app.delete("/v1/stress-periods/{period_id}", status_code=204)
    async def delete_stress_period(period_id: str, patient: Patient = Depends(current_patient),
                                   s: Services = Depends(svc)) -> None:
        if not await s.store.delete_stress_period(patient.id, period_id):
            raise HTTPException(404, "not_found")

    # ------------------------------------------------------------ insights

    @app.get("/v1/insights/patterns")
    async def patterns(scope: str = "all", patient: Patient = Depends(current_patient), s: Services = Depends(svc)) -> dict:
        if scope not in SCOPES:
            raise HTTPException(422, "bad_scope")
        return await s.insights.patterns(patient, scope)

    @app.get("/v1/insights/periods")
    async def periods(patient: Patient = Depends(current_patient), s: Services = Depends(svc)) -> dict:
        return await s.insights.periods(patient)

    @app.post("/v1/insights/periods/decision")
    async def period_decision(body: PeriodDecision, patient: Patient = Depends(current_patient),
                              s: Services = Depends(svc)) -> dict:
        current = await s.insights.periods(patient)
        if not any(p["kind"] == "flare" and p["start"] == body.start.isoformat() for p in current["periods"]):
            raise HTTPException(404, "no_such_period")
        decisions = await s.store.period_decisions(patient.id)
        if body.decision == "confirm":
            decisions.confirmed.add(body.start)
        else:  # the user's answer wins, and the same period isn't proposed again
            decisions.confirmed.discard(body.start)
            decisions.rejected.add(body.start)
        await s.store.save_period_decisions(patient.id, decisions)
        return await s.insights.periods(patient)

    @app.post("/v1/insights/periods/manual", status_code=201)
    async def manual_flare(body: ManualFlareIn, patient: Patient = Depends(current_patient), s: Services = Depends(svc)) -> dict:
        today = s.insights.today()
        if body.start > today or (body.end is not None and (body.end < body.start or body.end > today)):
            raise HTTPException(422, "bad_date_range")
        decisions = await s.store.period_decisions(patient.id)
        decisions.manual.append(ManualFlare(body.start, body.end))
        await s.store.save_period_decisions(patient.id, decisions)
        return await s.insights.periods(patient)

    @app.get("/v1/insights/flare-risk")
    async def risk(patient: Patient = Depends(current_patient), s: Services = Depends(svc)) -> dict:
        return await s.insights.flare_risk(patient)

    @app.get("/v1/reports/previsit")
    async def previsit(days: int = Query(default=90, ge=14, le=180), patient: Patient = Depends(current_patient),
                       s: Services = Depends(svc)) -> dict:
        return await s.insights.report(patient, days)

    return app


def _format(event: Event) -> str:
    return f"event: {event.name}\ndata: {json.dumps(event.data, ensure_ascii=False)}\n\n"


async def _sse(events: AsyncIterator[Event]) -> AsyncIterator[str]:
    try:
        async for event in events:
            yield _format(event)
    except Exception:  # never leak internals to the client; the flow already saved what it could
        log.exception("meal check failed")
        yield _format(Event("error", {"code": "internal_error"}))


def app() -> FastAPI:  # uvicorn --factory happygut_api.main:app
    return create_app()
