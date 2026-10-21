# HappyGut Constitution

## Core Principles

### I. Hero Flow First
The meal check is the product: photo or Bangla/English/Banglish text → graded personal verdict with reasons, citations and a gentler alternative → meal logged → Personal Gut Graph updated. Every plan and task is ranked by how directly it serves this flow.
- Tier A work (real and working in the demo) is finished before tier B work starts (see `docs/portal/submission-scope.md`).
- Tier C items (designed / roadmap) never appear in the live demo or video as if they work.

### II. Safety Before Intelligence (NON-NEGOTIABLE)
- A food is never labelled "safe". Verdicts are 🟢 Likely OK for you · 🟡 Caution · 🔴 Likely trigger for you · ⚪ Not sure.
- Red-flag symptoms (heavy bleeding, fever with abdominal pain, signs of obstruction, severe dehydration) stop all diet advice and direct the user to a clinician or emergency care.
- Stricturing Crohn's rules (avoid insoluble fibre, skins, seeds, nuts) are applied before any LLM output.
- The system never suggests starting, stopping or changing medication. Adherence reminders and logging only.

### III. The LLM Never Decides (NON-NEGOTIABLE)
LLMs handle perception (photos, labels, Bangla text) and explanation. The verdict is computed by a deterministic, unit-tested engine (`engine/`) from knowledge-graph, guideline and personal evidence. An explanation that disagrees with the engine's verdict is rejected by the output guard.

### IV. Evidence or "Not sure"
- Every health claim cites retrieved evidence: a Rule Card and its paper, composition data, or the user's own history.
- Weak or missing evidence produces ⚪ "Not sure" or a clarifying question, never a guess.
- Only legally licensed data is ingested, and each source's licence is recorded in `docs/03-data.md` before ingestion.

### V. Privacy by Architecture
- Text that may contain PII is scrubbed by a local model on team hardware before any cloud AI call. Cloud free-tier APIs receive only food photos and de-identified text.
- No real patient data in the repo or the prototype. Simulated data carries `is_synthetic = true` and is labelled "simulated" wherever it is shown.
- Secrets live only in `.env` files that are never committed.

### VI. Bangla-First
Every user-facing string exists in both Bangla and English (i18n files, no hard-coded text). Native Bangla speakers review generated Bangla before release.

### VII. Measured, Not Claimed
- Quality is shown with evaluation sets and numbers: verdict accuracy, red-flag recall, retrieval metrics, trigger recovery.
- CI blocks merges if red-flag recall drops below 100% or verdict accuracy drops by more than 2 points.
- Portal answers, README, /docs and the video must match what is actually built.

### VIII. Free and Simple
- Only free tiers that need no card: Supabase, Neo4j AuraDB Free, Google AI Studio (Gemini), Groq, Hugging Face Spaces, Vercel, Tailscale, ngrok, Langfuse Hobby, GitHub, plus self-hosted open source. No Google Cloud / Vertex, AWS or paid domains.
- The fewest moving parts that do the job. A new service or framework needs a written reason in the relevant decision log.

## Technology Constraints
- Frontend: React + Vite PWA, Tailwind, shadcn/ui, Zod, react-i18next (bn/en). Hosted on Vercel.
- Backend: Python 3.11, FastAPI, Pydantic v2, LangGraph + Pydantic-AI, LiteLLM. Docker on Hugging Face Spaces.
- Data: Supabase (Postgres + pgvector + pg_trgm + Storage + Auth), Neo4j AuraDB Free, DuckDB/Parquet for evaluation data.
- Local AI: Ollama on the team GPU machine (12 GB VRAM), reached through Tailscale Funnel behind an API-key gateway. The app keeps working with cloud models only when that machine is offline.
- Interfaces: REST (`/v1`, OpenAPI) and MCP servers (FastMCP; stdio + Streamable HTTP; read-only tools).

## Development Workflow and Quality Gates
- Spec-Kit flow per feature: `/speckit-specify` → `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`. Specs live in `specs/NNN-name/`.
- One GitHub issue per task and one pull request per step. AI-generated code is reviewed by a named team member before merge.
- Gates: every verdict-engine rule has a unit test; parsers have golden-file tests; the eval suite runs in CI on prompt, model or retrieval changes.
- Long prompts live in `prompts/runtime/` as versioned files, never inline in code. Build prompts are recorded in `prompts/build/`.
- Decisions are recorded in the decision log of the relevant `docs/` file.

## Governance
This constitution takes precedence over other practices in this repository. `CLAUDE.md` and `AGENTS.md` carry the same rules for coding agents and must stay consistent with it. Amendments are made by pull request with a one-line reason, reviewed by the Team Leader, and versioned semantically (MAJOR: a principle removed or redefined; MINOR: a principle or section added; PATCH: wording). Every spec and plan includes a constitution check before implementation starts.

**Version**: 1.0.0 | **Ratified**: 2026-10-21 | **Last Amended**: 2026-10-21
