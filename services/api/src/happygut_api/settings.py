"""Configuration from environment variables (see the repo's .env.example)."""

from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    # Reads the repo-root .env on Windows; on Hugging Face Spaces the values come from Space secrets.
    model_config = SettingsConfigDict(env_file=(REPO_ROOT / ".env", ".env"), env_file_encoding="utf-8", extra="ignore")

    # Supabase
    supabase_url: str = ""
    supabase_db_url: str = ""  # session pooler connection string (service access, backend only)
    jwt_audience: str = "authenticated"

    # Models (Google AI Studio and Groq free tiers). Exact model versions are stored with every meal check.
    gemini_api_key: str = ""
    groq_api_key: str = ""
    # Light models first: Flash-Lite and Groq answer in 1-2 s, while full Flash was overloaded (503) or timing
    # out (504) on the free tier in testing (2026-11-15). The meal-check target is a verdict in under 5 s.
    perception_model: str = "gemini-flash-lite-latest"
    perception_fallback_model: str = "gemini-flash-latest"
    explanation_model: str = "gemini-flash-lite-latest"
    explanation_fallback_model: str = "openai/gpt-oss-120b"  # Groq
    # Configured names are checked against what the keys can use at start-up; unavailable ones are replaced.
    resolve_models: bool = True
    gemini_base_url: str = ""  # tests / proxies only
    model_timeout_s: float = 12.0  # per model attempt, so a stuck model hands over quickly; a call allows 2.5x this

    # Knowledge
    seeds_dir: Path = REPO_ROOT / "data" / "seeds"
    prompts_dir: Path = REPO_ROOT / "prompts" / "runtime"
    # Development only: load draft seeds too. Verdicts are then labelled as based on unreviewed knowledge.
    include_draft_seeds: bool = False

    # PII
    pii_presidio: bool = False
    pii_bengali_ner_model: str = ""  # Hugging Face model id; empty = disabled. Record its licence in docs/03-data.md first.

    # Images
    max_image_bytes: int = 8 * 1024 * 1024
    max_image_side: int = 1536

    # Demo mode: a one-tap demo account with a simulated patient, held in memory (no Supabase needed).
    demo_mode: bool = False
    # Passwords for the three test accounts (nusrat@ / rafi@ / ayesha@happygut.test). An empty one gets a
    # random password for that run, printed in the start-up log. Use throw-away values: judges see them.
    test_password_nusrat: str = ""
    test_password_rafi: str = ""
    test_password_ayesha: str = ""
    session_secret: str = ""  # signs session tokens; empty = a new key per start (everyone signs in again)
    # Tracing to Langfuse Cloud (needs the "tracing" extra). Empty keys = no tracing.
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    # Bearer token for /v1/jobs/* (called by n8n). Empty = the job endpoints are switched off.
    jobs_token: str = ""
    timezone: str = "Asia/Dhaka"
    # The live /docs page. The admin page needs a password of at least 12 characters (empty = no admin page).
    # Visibility defaults; an admin can change them at /docs/admin until the next restart.
    docs_admin_password: str = ""
    docs_visible: bool = True
    docs_starts_at: datetime | None = None  # with a time zone, e.g. 2026-11-20T00:00:00+06:00
    docs_ends_at: datetime | None = None

    # CORS for the PWA
    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
