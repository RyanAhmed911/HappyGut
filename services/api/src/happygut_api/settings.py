"""Configuration from environment variables (see the repo's .env.example)."""

from __future__ import annotations

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
    perception_model: str = "gemini-flash-latest"
    perception_fallback_model: str = "gemini-flash-lite-latest"
    explanation_model: str = "gemini-flash-latest"
    explanation_fallback_model: str = "llama-3.3-70b-versatile"  # Groq
    model_timeout_s: float = 20.0

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

    # CORS for the PWA
    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
