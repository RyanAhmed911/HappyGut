"""FastAPI app: /v1 REST API with a streamed (SSE over POST) meal check."""

from __future__ import annotations

import json
import logging
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, Literal

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from happygut_engine import DEFAULT_CONFIG

from . import __version__
from .agents import PydanticExplainer, PydanticPerceiver, build_model
from .auth import AuthError, SupabaseVerifier, Verifier
from .flow import Event, MealCheckFlow
from .images import ImageRejected, sanitise
from .knowledge import Knowledge, MemoryKnowledge
from .pii import build_scrubber
from .prompts import load_prompt
from .settings import Settings, get_settings
from .store import MemoryStore, Patient, PostgresStore, Store

log = logging.getLogger("happygut.api")
MAX_TEXT = 1000


class Feedback(BaseModel):
    answer: Literal["right", "wrong", "not_sure"]


@dataclass
class Services:
    settings: Settings
    knowledge: Knowledge
    store: Store
    verifier: Verifier
    flow: MealCheckFlow


def build_services(settings: Settings) -> Services:
    knowledge = MemoryKnowledge.from_seeds(settings.seeds_dir, include_drafts=settings.include_draft_seeds)
    store: Store = PostgresStore(settings.supabase_db_url) if settings.supabase_db_url else MemoryStore()
    perceiver = PydanticPerceiver(
        build_model([settings.perception_model, settings.perception_fallback_model], settings.gemini_api_key, settings.groq_api_key),
        load_prompt(settings.prompts_dir, "meal-perception"), settings.model_timeout_s,
    )
    explainer = PydanticExplainer(
        build_model([settings.explanation_model, settings.explanation_fallback_model], settings.gemini_api_key, settings.groq_api_key),
        load_prompt(settings.prompts_dir, "meal-explanation"), settings.model_timeout_s,
    )
    scrubber = build_scrubber(settings.pii_presidio, settings.pii_bengali_ner_model, knowledge.all_names())
    flow = MealCheckFlow(knowledge, perceiver, explainer, scrubber, store)
    return Services(settings, knowledge, store, SupabaseVerifier(settings.supabase_url, settings.jwt_audience), flow)


def create_app(services: Services | None = None) -> FastAPI:
    holder: dict[str, Services] = {}

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        holder["s"] = services or build_services(get_settings())
        counts = holder["s"].knowledge.counts()
        log.info("knowledge loaded: %s (reviewed only: %s)", counts, holder["s"].knowledge.reviewed_only)
        yield

    settings = services.settings if services else get_settings()
    app = FastAPI(title="HappyGut API", version=__version__, lifespan=lifespan,
                  description="Self-management support, not a medical device. Verdicts come from the HappyGut engine.")
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET", "POST"],
                       allow_headers=["Authorization", "Content-Type"])

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

    @app.get("/v1/health")
    async def health(s: Services = Depends(svc)) -> dict:
        return {
            "status": "ok",
            "version": __version__,
            "engine_version": DEFAULT_CONFIG.version,
            "knowledge": {**s.knowledge.counts(), "reviewed_only": s.knowledge.reviewed_only},
            "storage": type(s.store).__name__,
        }

    @app.post("/v1/meal-checks")
    async def meal_check(
        text: str | None = Form(default=None),
        lang: Literal["bn", "en"] | None = Form(default=None),
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
        language = lang or patient.language
        return StreamingResponse(_sse(s.flow.stream(patient, language, text, clean)), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

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
