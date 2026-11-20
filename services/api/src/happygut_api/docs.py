"""The live /docs module: a public pitch deck and technical documentation page.

The page's text lives in the web app (Bangla and English). This module serves what changes:
- whether the page is open right now (an on / off switch and an optional time window),
- live system data (versions, knowledge, models, features, API endpoints, usage counts),
- admin edits: replaced section text, section order and the team list.

Admin edits are kept in memory, like the rest of the prototype's data: a restart goes back to
the defaults from the environment (DOCS_VISIBLE, DOCS_STARTS_AT, DOCS_ENDS_AT). The admin page
can download everything as JSON so an edit can be committed to the repository.
"""

from __future__ import annotations

import hmac
import json
import secrets
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from importlib import resources
from typing import Any, Literal

import jwt
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field, model_validator

# The sections the web app renders; admins may replace the text of any of them or reorder them.
PITCH_SECTIONS = ("problem", "solution", "why_now", "demo", "market", "business_model", "traction", "competition",
                  "advantage", "go_to_market", "team", "vision")
TECH_SECTIONS = ("overview", "features", "architecture", "data_flow", "stack", "api", "data_layer", "ai_layer",
                 "roadmap", "performance", "security", "analytics", "changelog")
SECTION_IDS = PITCH_SECTIONS + TECH_SECTIONS

# Team Cinnamon Syrups (roles per AIBC guide §13.2; all five also built frontend and backend).
# Photos are cropped, resized and metadata-free copies in apps/web/public/team/.
DEFAULT_TEAM: tuple[dict[str, str], ...] = (
    {"name": "Ryan Ahmed", "role": "Team Leader · Frontend & Backend", "role_bn": "টিম লিডার · ফ্রন্টএন্ড ও ব্যাকএন্ড",
     "email": "ryanahmed9110@gmail.com", "photo_url": "/team/ryan-ahmed.jpg"},
    {"name": "Nusayba Mahfuza Zaman", "role": "Presentation & Communication Lead", "role_bn": "প্রেজেন্টেশন ও যোগাযোগ প্রধান",
     "email": "nusaybazaman3@gmail.com", "photo_url": "/team/nusayba-mahfuza-zaman.jpg"},
    {"name": "Raiyan Rahman", "role": "Frontend & Backend Developer", "role_bn": "ফ্রন্টএন্ড ও ব্যাকএন্ড ডেভেলপার",
     "email": "c.raiyan.rahman0@gmail.com", "photo_url": "/team/raiyan-rahman.jpg"},
    {"name": "Al-Saihan Tajvi", "role": "Business Analyst / Data Scientist", "role_bn": "বিজনেস অ্যানালিস্ট / ডেটা সায়েন্টিস্ট",
     "email": "al.saihan.bafsd.5@gmail.com", "photo_url": "/team/al-saihan-tajvi.jpg"},
    {"name": "Zarin Tasnim", "role": "Business Analyst / Data Scientist", "role_bn": "বিজনেস অ্যানালিস্ট / ডেটা সায়েন্টিস্ট",
     "email": "zarin_nadia@yahoo.com", "photo_url": "/team/zarin-tasnim.jpg"},
)
TEAM_NAME = "Cinnamon Syrups"
MIN_PASSWORD = 12
ADMIN_TTL_S = 8 * 3600
MAX_HISTORY = 50


class DocsSettingsIn(BaseModel):
    visible: bool
    starts_at: datetime | None = None
    ends_at: datetime | None = None

    @model_validator(mode="after")
    def _window(self) -> DocsSettingsIn:
        for name in ("starts_at", "ends_at"):
            value = getattr(self, name)
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{name} needs a time zone")
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class SectionIn(BaseModel):
    en: str = Field(min_length=1, max_length=4000)
    bn: str = Field(min_length=1, max_length=4000)


class OrderIn(BaseModel):
    pitch: list[str] = Field(max_length=len(PITCH_SECTIONS))
    tech: list[str] = Field(max_length=len(TECH_SECTIONS))

    @model_validator(mode="after")
    def _complete(self) -> OrderIn:
        if sorted(self.pitch) != sorted(PITCH_SECTIONS) or sorted(self.tech) != sorted(TECH_SECTIONS):
            raise ValueError("each list must hold every section of its part exactly once")
        return self


class TeamMemberIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    role: str = Field(default="", max_length=80)
    role_bn: str = Field(default="", max_length=80)
    email: str = Field(default="", max_length=120, pattern=r"^$|^[^@\s]+@[^@\s]+\.[^@\s]+$")
    # A photo in the web app's public/team folder, or any https link.
    photo_url: str = Field(default="", max_length=500, pattern=r"^$|^https://\S+$|^/team/[a-z0-9-]+\.(jpg|png|webp)$")


class TeamIn(BaseModel):
    team_name: str = Field(default=TEAM_NAME, max_length=80)
    members: list[TeamMemberIn] = Field(min_length=1, max_length=12)


class LoginIn(BaseModel):
    password: str = Field(min_length=1, max_length=200)


@dataclass
class DocsState:
    visible: bool = True
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    sections: dict[str, dict[str, str]] = field(default_factory=dict)
    pitch_order: list[str] = field(default_factory=lambda: list(PITCH_SECTIONS))
    tech_order: list[str] = field(default_factory=lambda: list(TECH_SECTIONS))
    team_name: str = TEAM_NAME
    team: list[dict[str, str]] = field(default_factory=lambda: [dict(m) for m in DEFAULT_TEAM])
    history: list[dict[str, str]] = field(default_factory=list)
    updated_at: datetime | None = None

    def status(self, now: datetime) -> tuple[bool, Literal["open", "off", "not_yet", "ended"]]:
        if not self.visible:
            return False, "off"
        if self.starts_at and now < self.starts_at:
            return False, "not_yet"
        if self.ends_at and now > self.ends_at:
            return False, "ended"
        return True, "open"

    def window(self) -> dict[str, Any]:
        return {"visible": self.visible, "starts_at": _iso(self.starts_at), "ends_at": _iso(self.ends_at)}

    def record(self, change: str, now: datetime) -> None:
        self.updated_at = now
        self.history = [{"at": now.isoformat(), "change": change}, *self.history][:MAX_HISTORY]

    def content(self) -> dict[str, Any]:
        """What the public page needs besides live data: replaced text, order and team."""
        return {"sections": self.sections, "order": {"pitch": self.pitch_order, "tech": self.tech_order},
                "team": {"name": self.team_name, "members": self.team}, "updated_at": _iso(self.updated_at)}

    def export(self) -> dict[str, Any]:
        return {**self.window(), **self.content(), "history": self.history}


class DocsAdmin:
    """Admin sign-in for the docs page: one shared password from the environment, short-lived signed tokens."""

    WINDOW_S, MAX_FAILURES = 300, 5

    def __init__(self, password: str, secret: str = "") -> None:
        self.password = password if len(password) >= MIN_PASSWORD else ""
        self._key = (secret or secrets.token_urlsafe(32)) + ":docs-admin"
        self._failures: list[float] = []

    @property
    def enabled(self) -> bool:
        return bool(self.password)

    def locked(self) -> bool:
        self._failures = [t for t in self._failures if time.time() - t < self.WINDOW_S]
        return len(self._failures) >= self.MAX_FAILURES

    def login(self, password: str) -> str | None:
        if not self.enabled or not hmac.compare_digest(password.encode(), self.password.encode()):
            self._failures.append(time.time())
            return None
        return jwt.encode({"sub": "docs-admin", "aud": "happygut-docs", "exp": int(time.time()) + ADMIN_TTL_S},
                          self._key, algorithm="HS256")

    def check(self, authorization: str | None) -> bool:
        scheme, _, token = (authorization or "").partition(" ")
        if not self.enabled or scheme.lower() != "bearer" or not token:
            return False
        try:
            jwt.decode(token, self._key, algorithms=["HS256"], audience="happygut-docs")
        except jwt.PyJWTError:
            return False
        return True


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def endpoints(routes: list[Any]) -> list[dict[str, str]]:
    """The API's own route table, so the documentation can never list an endpoint that doesn't exist."""
    out = []
    for route in routes:
        if not isinstance(route, APIRoute) or not route.path.startswith("/v1/"):
            continue
        path = route.path
        if path.startswith("/v1/docs/admin") and path != "/v1/docs/admin/login":
            access = "docs_admin"
        elif path.startswith("/v1/jobs/"):
            access = "job_token"
        elif path in ("/v1/health", "/v1/auth/login", "/v1/docs", "/v1/docs/status", "/v1/docs/admin/login"):
            access = "public"
        else:
            access = "patient"
        for method in sorted(route.methods - {"HEAD", "OPTIONS"}):
            out.append({"method": method, "path": path, "access": access, "summary": (route.summary or route.name).replace("_", " ")})
    return sorted(out, key=lambda e: (e["path"], e["method"]))


def flare_model_card() -> dict[str, Any] | None:
    try:
        card = json.loads(resources.files("happygut_api").joinpath("models/flare-risk-v1.json").read_text())
    except (OSError, ValueError):
        return None
    test = card.get("test", {})
    return {"version": card.get("version"), "trained": card.get("trained"), "question": card.get("question"),
            "base_rate": test.get("base_rate"), "v1": test.get("v1"), "v0": test.get("v0"),
            "features": len(card.get("features", []))}


def usage(store: Any) -> dict[str, int] | None:
    """Counts from the in-memory store (the prototype's sample accounts and what judges add); None on other storage."""
    tables = ("patients", "meal_checks", "diary", "red_flags", "weights", "medications", "appointments", "stress_periods")
    if not all(hasattr(store, t) for t in tables):
        return None

    def nested(table: dict) -> int:
        return sum(len(v) for v in table.values())

    return {
        "accounts": len(store.patients),
        "meal_checks": len(store.meal_checks),
        "diary_days": nested(store.diary),
        "red_flag_escalations": len(store.red_flags),
        "weigh_ins": nested(store.weights),
        "medicines": nested(store.medications),
        "appointments": nested(store.appointments),
        "stressful_periods": nested(store.stress_periods),
    }


def features(models: dict[str, bool], tracing_on: bool, jobs_on: bool, flare_model: bool) -> list[dict[str, str]]:
    """Feature matrix with a status computed from the running system, not typed by hand."""
    live, off = "live", "off"
    rows = [
        ("meal_check_text", live), ("meal_check_photo", live if models.get("perception") else off),
        ("ai_explanation", live if models.get("explanation") else "template"), ("red_flags", live),
        ("stricture_rules", live), ("nightly_diary", live), ("pattern_finder", live), ("periods", live),
        ("flare_risk_v0", live), ("flare_risk_v1", live if flare_model else off), ("doctor_report", live),
        ("medicines_tests", live), ("weight", live), ("food_guide", live), ("bangla_english", live),
        ("tracing", live if tracing_on else off), ("scheduled_jobs", live if jobs_on else off),
        ("mcp_servers", "built"), ("real_signup", "planned"), ("neo4j_pgvector", "planned"),
        ("clinic_pilot", "planned"), ("research_aggregates", "planned"),
    ]
    return [{"id": key, "status": status} for key, status in rows]


def now_utc() -> datetime:
    return datetime.now(UTC)
