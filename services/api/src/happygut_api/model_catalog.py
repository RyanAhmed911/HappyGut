"""Which models can these keys actually use? Ask the providers, then pick the best match.

Provider model lists change: names are retired (Groq dropped llama-3.3-70b-versatile) and
aliases exist only on some API versions. At start-up the backend lists the models each key
can use and replaces any configured name that isn't there with the best available one, so
the app keeps working without anyone editing model names. If listing fails (no network,
no key), the configured names are used unchanged.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

import httpx

log = logging.getLogger("happygut.models")

GEMINI_API = "https://generativelanguage.googleapis.com"
GEMINI_API_VERSION = "v1beta"  # the "-latest" aliases and JSON-schema tools live here; google-genai 3 defaults to v1
GROQ_API = "https://api.groq.com/openai/v1"

# Groq text models, best first. Anything else chat-capable is a last resort.
GROQ_PREFERENCE = (
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "moonshotai/kimi-k2-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "openai/gpt-oss-20b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.1-8b-instant",
)
_GROQ_NOT_CHAT = re.compile(r"whisper|guard|tts|playai|distil|compound|orpheus|prompt", re.I)

_GEMINI_STABLE = re.compile(r"^gemini-(\d+(?:\.\d+)?)-flash(-lite)?$")
_GEMINI_PREVIEW = re.compile(r"^gemini-(\d+(?:\.\d+)?)-flash(-lite)?-preview(?:-[\w-]+)?$")


@dataclass
class Catalog:
    gemini: list[str] | None = None  # None = couldn't list (keep configured names)
    groq: list[str] | None = None
    errors: list[str] = field(default_factory=list)


def list_gemini(api_key: str, base_url: str = GEMINI_API, timeout: float = 8.0) -> list[str]:
    """Model ids (without "models/") that support generateContent."""
    names: list[str] = []
    token = ""
    with httpx.Client(base_url=base_url, timeout=timeout, headers={"x-goog-api-key": api_key}) as client:
        for _ in range(10):  # pages
            params = {"pageSize": 1000, **({"pageToken": token} if token else {})}
            r = client.get(f"/{GEMINI_API_VERSION}/models", params=params)
            r.raise_for_status()
            data = r.json()
            for m in data.get("models", []):
                if "generateContent" in m.get("supportedGenerationMethods", []):
                    names.append(m["name"].removeprefix("models/"))
            token = data.get("nextPageToken", "")
            if not token:
                break
    return names


def list_groq(api_key: str, base_url: str = GROQ_API, timeout: float = 8.0) -> list[str]:
    with httpx.Client(base_url=base_url, timeout=timeout, headers={"Authorization": f"Bearer {api_key}"}) as client:
        r = client.get("/models")
        r.raise_for_status()
        return [m["id"] for m in r.json().get("data", []) if m.get("active", True)]


def fetch(gemini_key: str, groq_key: str, gemini_base_url: str = GEMINI_API, groq_base_url: str = GROQ_API) -> Catalog:
    cat = Catalog()
    if gemini_key:
        try:
            cat.gemini = list_gemini(gemini_key, gemini_base_url)
        except Exception as exc:  # any failure: keep the configured names
            cat.errors.append(f"Gemini model list: {type(exc).__name__}: {exc}")
    if groq_key:
        try:
            cat.groq = list_groq(groq_key, groq_base_url)
        except Exception as exc:
            cat.errors.append(f"Groq model list: {type(exc).__name__}: {exc}")
    return cat


def _version(match: re.Match[str]) -> float:
    return float(match.group(1))


def best_gemini(available: list[str], lite: bool) -> str | None:
    """The "-latest" alias if offered, else the newest stable Flash (or Flash-Lite), else the newest preview."""
    alias = "gemini-flash-lite-latest" if lite else "gemini-flash-latest"
    if alias in available:
        return alias
    for pattern in (_GEMINI_STABLE, _GEMINI_PREVIEW):
        found = [(m, n) for n in available if (m := pattern.match(n)) and bool(m.group(2)) == lite]
        if found:
            return max(found, key=lambda x: (_version(x[0]), x[1]))[1]
    return None


def best_groq(available: list[str]) -> str | None:
    for name in GROQ_PREFERENCE:
        if name in available:
            return name
    chat = [n for n in available if not _GROQ_NOT_CHAT.search(n)]
    return sorted(chat)[0] if chat else None


def resolve(name: str, cat: Catalog, lite: bool = False) -> tuple[str, str | None]:
    """(model to use, note). A configured name that the key can use is always kept."""
    if not name:
        return name, None
    if name.startswith("gemini"):
        if cat.gemini is None or name in cat.gemini:
            return name, None
        pick = best_gemini(cat.gemini, lite)
    else:
        if cat.groq is None or name in cat.groq:
            return name, None
        pick = best_groq(cat.groq)
    if pick is None:
        return name, f"{name} is not available for this key and no replacement was found"
    return pick, f"{name} is not available for this key; using {pick}"


@dataclass
class ModelChoice:
    perception: list[str]
    explanation: list[str]
    notes: list[str]


def choose(settings, catalog: Catalog | None = None) -> ModelChoice:
    """Resolve the configured perception and explanation chains against what the keys can use."""
    cat = catalog if catalog is not None else fetch(
        settings.gemini_api_key, settings.groq_api_key, settings.gemini_base_url or GEMINI_API)
    notes = list(cat.errors)

    def chain(primary: str, fallback: str) -> list[str]:
        # The primary is a full Flash model; a Gemini fallback is the light model of the same family.
        first, n1 = resolve(primary, cat, lite=False)
        second, n2 = resolve(fallback, cat, lite="lite" in fallback)
        notes.extend(n for n in (n1, n2) if n)
        return list(dict.fromkeys(m for m in (first, second) if m))

    perception = chain(settings.perception_model, settings.perception_fallback_model)
    explanation = chain(settings.explanation_model, settings.explanation_fallback_model)
    for note in notes:
        log.warning("models: %s", note)
    return ModelChoice(perception, explanation, notes)
