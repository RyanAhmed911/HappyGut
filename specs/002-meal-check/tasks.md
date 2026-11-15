# Tasks: Meal check (hero flow)

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Phase 1: Backend foundation
- [x] T001 `services/api` package: settings, health endpoint, pytest setup, CI job
- [x] T002 Supabase JWT verification (JWKS, audience `authenticated`) → patient profile lookup
- [~] T003 PII scrubber: Bangladesh rules (phones, NID, birth registration, email, name cues, Bangla digits) + Presidio (on in the Docker image; dish names protected) + Bengali NER adapter. **Open:** choose the Bengali NER model and record its licence
- [x] T004 Image checks: type and size limits, downscale, EXIF/GPS strip by re-encoding

## Phase 2: Meal-check flow [US1, US2, US3, US4]
- [x] T005 Versioned runtime prompts: `meal-perception` v1, `meal-explanation` v1, and the loader
- [x] T006 Perception agent (photo or text → items with confidence, not-food flag, clarifying question); Gemini with fallback
- [x] T007 Knowledge adapter: dish resolution, components, Rule Cards, alternatives from approved seeds
- [x] T008 Verdict step: resolved and unresolved items → `assess_meal`; unresolved → ⚪
- [x] T009 Evidence packet + explanation agent (bn/en, cites IDs)
- [x] T010 Output guard (citations ⊆ evidence, no contradicting verdict label, banned wording) + one retry + template fallback
- [x] T011 LangGraph graph with early exits (red flag, not food) and staged SSE events
- [~] T012 Storage: meal checks (evidence IDs, model / prompt / engine versions), red-flag events, feedback; memory and Postgres implementations [US5]. **Open:** run the Postgres store against Supabase (no database access from the build sandbox); photo upload to Storage
- [x] T013 Endpoints: `POST /v1/meal-checks` (SSE), `GET /v1/meal-checks/{id}`, `POST /v1/meal-checks/{id}/feedback`
- [~] T014 Dockerfile for Hugging Face Spaces. The image's file layout was installed and started in the sandbox (health OK, auth enforced); **open:** a real `docker build` and the Space itself (step 5)

## Phase 3: Frontend [US1, US2, US4]
- [~] T015 PWA skeleton (React + Vite + Tailwind + Radix + react-i18next bn/en), demo sign-in. **Open:** Supabase Auth and the onboarding profile
- [x] T016 Scan / type screen, streamed verdict card (dishes → verdict → explanation, evidence bar, alternative), escalation screen
- [x] T017 Meal history and "Was this right for you?" feedback

## Phase 4: Proof and wiring
- [ ] T018 Live smoke test against Gemini/Groq on Windows with real keys; record latency (p90 < 5 s)
- [ ] T019 Neo4j knowledge adapter and guideline hybrid RAG in the evidence packet (after 001 T008, T009, T013)
- [ ] T020 Eval sets: 200-food verdict set, red-flag suite, 30 typed inputs, photo set → `run-evals`
