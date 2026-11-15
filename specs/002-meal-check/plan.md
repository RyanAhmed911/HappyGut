# Implementation Plan: Meal check (hero flow)

**Branch**: `002-meal-check` (worked on `claude/adoring-newton-9o7big`) · **Date**: 2026-11-07 · **Spec**: [spec.md](spec.md)

## Summary
A FastAPI backend (`services/api`) takes a photo or Bangla/English text and streams back: the dishes found → the engine's verdict → a cited explanation in the patient's language. A LangGraph graph runs the steps in order: red-flag sentinel → PII scrub → perception (Gemini, Groq fallback) → dish resolution in the knowledge layer → deterministic verdict engine → explanation from the evidence packet only → output guard → store. The PWA (`apps/web`) is a separate task in this spec.

## Technical Context
- **Language**: Python 3.11 (API), TypeScript (PWA, later task)
- **Dependencies**: FastAPI, Pydantic v2, pydantic-settings, LangGraph (flow), Pydantic-AI (typed perception and explanation agents, `FallbackModel` across Gemini and Groq), Pillow (image checks, EXIF strip), psycopg 3 (Postgres), PyJWT (Supabase JWT via JWKS); optional `pii` extra: Presidio + a Bengali NER model
- **Storage**: Supabase Postgres via the session pooler (`events.meal_checks`, `events.verdict_feedback`, `events.red_flag_events`, `core.patients`); these schemas aren't exposed through the Data API, so the backend connects directly as the service role
- **Knowledge**: approved seeds loaded in memory at start-up (the same `MemoryGraph` the foodgraph MCP uses offline). A Neo4j adapter and guideline RAG (pgvector) plug in behind the same interface once the loader (001 T013) and the corpus (001 T008–T009) exist
- **Testing**: pytest with fake perception/explanation agents, Pydantic-AI `TestModel` for the agent wiring, an in-memory store, and a locally signed ES256 JWT
- **Target**: Docker on Hugging Face Spaces (free CPU, port 7860)
- **Performance**: p90 < 5 s to verdict; dishes event first

## Constitution Check
| Principle | How this plan complies |
|---|---|
| I Hero flow first | This is the hero flow; nothing else is built before it works |
| II Safety | Sentinel runs first on raw text, before any model call; red flags stop the flow and are stored; stricture hard rules live in the engine; banned-wording guard (no "safe", no medication advice) |
| III LLM never decides | Verdicts come only from `happygut_engine.assess_meal`; the explanation never states a verdict label different from the engine's, or the guard rejects it |
| IV Evidence or Not sure | The explainer sees only the evidence packet and must cite its IDs; unresolved dishes and low confidence go to ⚪ with a clarifying question; only approved seeds load |
| V Privacy | Text scrubbed (Bangladesh rules + Presidio + Bengali NER when installed) before any cloud call; photos re-encoded without EXIF/GPS; nothing identifying is stored with a meal check |
| VI Bangla-first | Backend strings in `locales/bn.json` and `locales/en.json`; explanation language follows the patient profile |
| VII Measured | Model, prompt and engine versions stored with every meal check; prompts versioned in `prompts/runtime/` |
| VIII Free and simple | Gemini (AI Studio) + Groq free tiers; one backend; no new services |

## Project Structure
```
services/api/
  pyproject.toml, Dockerfile, README.md
  src/happygut_api/
    settings.py      environment configuration
    auth.py          Supabase JWT (JWKS) → user id
    pii.py           Bangladesh rules + optional Presidio / Bengali NER
    images.py        size / type checks, downscale, EXIF strip
    prompts.py       versioned prompt loader (prompts/runtime/<id>/vN.md)
    agents.py        perception + explanation agents (Pydantic-AI, Gemini → Groq fallback)
    knowledge.py     knowledge interface + in-memory implementation from approved seeds
    evidence.py      evidence packet for the explainer
    guard.py         output guard + deterministic template fallback
    flow.py          LangGraph meal-check graph
    store.py         patient / meal-check / feedback / red-flag storage (memory + Postgres)
    main.py          FastAPI app: /v1/health, /v1/meal-checks (SSE), /v1/meal-checks/{id}, /feedback
    locales/         bn.json, en.json
  tests/
prompts/runtime/meal-perception/v1.md
prompts/runtime/meal-explanation/v1.md
```

## Decisions
| # | Decision | Why |
|---|---|---|
| MC1 | Pydantic-AI `FallbackModel` instead of LiteLLM for provider fallback | Pydantic-AI is already the agent layer (AR5) and has typed outputs plus cross-provider fallback; adding LiteLLM would be a second client for the same job (Constitution VIII) |
| MC2 | Photo fallback goes to a second Gemini model (Flash-Lite, separate quota); text fallback goes to Groq Llama | Groq's production models are text-only |
| MC3 | Knowledge in memory from approved seeds | Always-on with no extra service; same queries as the MCP's offline mode; Neo4j adapter later |
| MC4 | Explanations may not state a verdict label; the UI shows the engine's label | Makes "explanation contradicts the verdict" checkable with simple phrase lists in both languages |
| MC5 | Guard failure → one regeneration → deterministic template built from Rule Card recommendations | The flow always completes with cited text |
| MC6 | SSE over `POST` (fetch streaming) | Photos need a POST body; `EventSource` only does GET |
