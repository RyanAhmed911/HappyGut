"""Model discovery: list what the keys can use, replace retired names, call Gemini on v1beta."""

from __future__ import annotations

import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from happygut_api import model_catalog as mc
from happygut_api.agents import PydanticPerceiver, build_model
from happygut_api.prompts import load_prompt
from happygut_api.settings import REPO_ROOT, Settings

GEMINI_MODELS = [
    {"name": "models/gemini-2.5-flash", "supportedGenerationMethods": ["generateContent", "countTokens"]},
    {"name": "models/gemini-2.5-flash-lite", "supportedGenerationMethods": ["generateContent"]},
    {"name": "models/gemini-3-flash", "supportedGenerationMethods": ["generateContent"]},
    {"name": "models/gemini-3-flash-lite", "supportedGenerationMethods": ["generateContent"]},
    {"name": "models/gemini-3.5-flash-preview-09-2026", "supportedGenerationMethods": ["generateContent"]},
    {"name": "models/gemini-3-flash-image", "supportedGenerationMethods": ["generateContent"]},
    {"name": "models/text-embedding-004", "supportedGenerationMethods": ["embedContent"]},
]
GROQ_MODELS = [{"id": "openai/gpt-oss-120b", "active": True}, {"id": "whisper-large-v3", "active": True},
               {"id": "llama-3.1-8b-instant", "active": True}]


@pytest.fixture
def fake_api():
    """A local stand-in for both providers. Records every request path."""
    seen: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, body: dict) -> None:
            data = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            seen.append(f"GET {self.path}")
            if self.path.startswith("/v1beta/models"):
                self._send(200, {"models": GEMINI_MODELS})
            elif self.path.startswith("/openai/v1/models"):
                self._send(200, {"data": GROQ_MODELS})
            else:
                self._send(404, {"error": {"message": "nope"}})

        def do_POST(self):
            seen.append(f"POST {self.path}")
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            args = {"is_food": True, "items": [{"name_en": "kacchi biryani", "confidence": 0.9}]}
            self._send(200, {"candidates": [{"content": {"role": "model", "parts": [
                {"functionCall": {"name": "final_result", "args": args}}]}, "finishReason": "STOP"}],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5}, "modelVersion": "gemini-3-flash"})

        def log_message(self, *a):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}", seen
    server.shutdown()


def test_best_gemini_prefers_alias_then_newest_stable():
    names = [m["name"].removeprefix("models/") for m in GEMINI_MODELS]
    assert mc.best_gemini(names, lite=False) == "gemini-3-flash"
    assert mc.best_gemini(names, lite=True) == "gemini-3-flash-lite"
    assert mc.best_gemini(names + ["gemini-flash-latest"], lite=False) == "gemini-flash-latest"
    assert mc.best_gemini(["gemini-3.5-flash-preview-09-2026"], lite=False) == "gemini-3.5-flash-preview-09-2026"
    assert mc.best_gemini(["text-embedding-004"], lite=False) is None


def test_best_groq_skips_audio_and_guard_models():
    assert mc.best_groq(["whisper-large-v3", "llama-3.1-8b-instant", "openai/gpt-oss-120b"]) == "openai/gpt-oss-120b"
    assert mc.best_groq(["whisper-large-v3", "meta-llama/llama-prompt-guard-2-86m", "qwen/qwen3-32b"]) == "qwen/qwen3-32b"


def test_resolve_keeps_available_names_and_replaces_retired_ones():
    cat = mc.Catalog(gemini=["gemini-2.5-flash", "gemini-2.5-flash-lite"], groq=["openai/gpt-oss-120b"])
    assert mc.resolve("gemini-2.5-flash", cat) == ("gemini-2.5-flash", None)
    assert mc.resolve("gemini-flash-latest", cat)[0] == "gemini-2.5-flash"
    assert mc.resolve("gemini-flash-lite-latest", cat, lite=True)[0] == "gemini-2.5-flash-lite"
    name, note = mc.resolve("llama-3.3-70b-versatile", cat)
    assert name == "openai/gpt-oss-120b" and "not available" in note
    assert mc.resolve("gemini-flash-latest", mc.Catalog(gemini=None)) == ("gemini-flash-latest", None)  # couldn't list


def test_choose_lists_both_providers(fake_api):
    base, seen = fake_api
    cat = mc.fetch("g-key", "q-key", gemini_base_url=base, groq_base_url=f"{base}/openai/v1")
    assert "gemini-3-flash" in cat.gemini and "text-embedding-004" not in cat.gemini and cat.groq
    choice = mc.choose(Settings(gemini_api_key="g", groq_api_key="q"), cat)
    assert choice.perception == ["gemini-3-flash", "gemini-3-flash-lite"]
    assert choice.explanation == ["gemini-3-flash", "openai/gpt-oss-120b"]
    assert any(p.startswith("GET /v1beta/models") for p in seen)


def test_listing_failure_keeps_configured_names():
    cat = mc.fetch("g-key", "", gemini_base_url="http://127.0.0.1:9")  # nothing listens there
    assert cat.gemini is None and cat.errors
    choice = mc.choose(Settings(gemini_api_key="g", groq_api_key=""), cat)
    assert choice.perception[0] == "gemini-flash-latest"


def test_gemini_calls_use_v1beta(fake_api):
    base, seen = fake_api
    model = build_model(["gemini-3-flash"], "g-key", "", gemini_base_url=base)
    agent = PydanticPerceiver(model, load_prompt(REPO_ROOT / "prompts" / "runtime", "meal-perception"))
    run = asyncio.run(agent.perceive(text="kacchi", image=None, lang="en"))
    assert run.output.items[0].name_en == "kacchi biryani"
    assert any(p.startswith("POST /v1beta/models/gemini-3-flash:generateContent") for p in seen), seen
