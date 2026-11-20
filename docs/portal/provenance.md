# Portal text: Data & AI provenance (required field)

> Updated 20 Nov 2026 to match what is built and deployed. Paste only the lists, not this note. Anything not listed here is not built yet (see `submission-scope.md`).

## Data sources
- Team-authored knowledge: 109 dishes eaten in Bangladesh (YAML seeds with ingredients, gut-relevant component levels and sources) and 25 Rule Cards
- Published IBD guidance behind the Rule Cards: 12 papers, each confirmed by DOI / PMID through the Europe PMC API, e.g. ESPEN guideline on clinical nutrition in IBD 2023 (PMID 36739756), IOIBD dietary guidance 2020 (PMID 32068150), AGA clinical practice update on diet 2024 (PMID 38276922). Open-access (CC BY 4.0) papers are quoted from the full text; for the others we use a short quotation from the published abstract or a citation only, as recorded on each card
- Weight-loss threshold: GLIM criteria (Cederholm et al. 2019, PMID 30920778, CC BY)
- Facts in the video and pitch: Shenoy et al. 2025 (PMID 39954693), Banerjee et al. 2022 (PMID 35178742), GBD 2017 IBD Collaborators (PMID 31648971), Ng et al. 2017 (PMID 29050646), Ghosh et al. 2023 (PMID 37283595)
- User input: meal photos, label and menu photos, typed text in Bangla or English; photos are never stored
- Synthetic, always labelled: a simulated cohort of 200 IBD patients × 120 days with known hidden contributors; three sample patient accounts for the demo; a team-written red-flag test set (29 emergency phrases, 30 ordinary messages)
- Not used: scraping, proprietary databases (e.g. Monash FODMAP), social-media posts, real patient records

## AI models
- Gemini Flash-Lite, falling back to Gemini Flash (Google AI Studio free tier): reads meal photos and text into dishes as JSON; writes the Bangla or English explanation
- gpt-oss-120b on Groq (free tier): fallback for explanations; Llama models on Groq as further backups
- Gemma 3 12B (local, Ollama, offline GPU job): suggested dish-name spellings, each accepted or rejected by an LLM judge
- BGE-M3 (local, offline GPU job): dish-name embeddings (not used by the live app yet)
- Microsoft Presidio + spaCy en_core_web_sm: name detection inside the PII scrub
- Custom models: LightGBM flare-risk model v1 with SHAP drivers (trained on simulated patients); Bayesian N-of-1 Flare Pattern Finder
- Claude (via Claude Code): development only, not at runtime; also the LLM judge for knowledge review

## Responsible AI
- The LLM never decides: verdicts come from a deterministic, unit-tested engine; AI only reads inputs and explains
- Graded verdicts, never "safe"; ⚪ "Not sure" when evidence is missing; every warning cites a Rule Card
- Red-flag symptoms stop diet advice and direct the user to a doctor or emergency care; no medication advice, ever
- Stricturing Crohn's safety rules are applied before any AI output
- Privacy: personal details removed inside our backend (Bangladesh rules + Presidio) before any cloud AI call; photos stripped of EXIF / GPS and never stored; the prototype holds no real patient data
- Free-tier cloud APIs only receive food photos and de-identified text
- Knowledge review: every dish, Rule Card, spelling and Bangla string is reviewed by an LLM judge following a written rubric (`docs/seed-review.md`); no clinician reviewed the knowledge
- Bias checks: red-flag results reported separately for English, Bangla and Bangla in English letters
- Transparency: evidence bars, citations, SHAP drivers on the flare estimate, a model card for the flare model, prompt and model versions stored with each meal check
- Honesty: simulated results always labelled; no fabricated traction or outcomes
- Human oversight: the team leader reviews and merges every change through pull requests that must pass CI
- Legally sourced data only, each source's licence recorded; positioned as self-management support, not a medical device

# Portal text: Tooling & IDE

## IDE / Editor
- VS Code + Claude Code (main AI coding agent: code, tests, reviews, documentation)

## Deployment method
- Frontend PWA: Vercel (Hobby, free)
- Backend API: FastAPI in Docker on Render (free web service)
- Team GPU (AMD Radeon RX 7700 XT, Ubuntu): finite offline jobs (Ollama + PyTorch on ROCm) that exchange files with the Windows machines through git; nothing live runs on it
- n8n: four workflows in `n8n/workflows`, run with Docker
- MCP servers: run locally (stdio) for Claude Code / Claude Desktop, or over Streamable HTTP with a bearer token
- Database for real users: Supabase Postgres migrations written and tested in CI (not live in the prototype)
- CI: GitHub Actions on every pull request (engine, backend, MCP servers, seeds, web app, database) plus a secret scan; Vercel preview per pull request

## Frameworks & libraries
- Frontend: React 19, Vite (PWA), Tailwind CSS, TanStack Query, Zod, react-i18next, Recharts
- Backend: FastAPI, Pydantic v2, pydantic-settings, PyJWT
- AI / agents: LangGraph, Pydantic-AI, MCP Python SDK
- ML: LightGBM (with SHAP values), NumPy
- Privacy: Microsoft Presidio, spaCy
- Data: PyYAML seeds, Supabase migrations (pg_trgm, pg_cron), PGlite for database tests
- Offline jobs: Ollama, sentence-transformers
- Ops: Langfuse (OpenTelemetry), n8n, pytest, Vitest, Playwright

## Context / memory files
- `CLAUDE.md`: Claude Code context, importing `AGENTS.md`
- `AGENTS.md`: non-negotiable product rules for every coding agent
- `.claude/skills/`: repeatable procedures (add-dish, add-rule-card, new-prompt-version, run-evals) plus Spec-Kit skills
- `.specify/memory/constitution.md` + `specs/*/spec.md, plan.md, tasks.md` (Spec-Kit)
- `docs/` decision logs (strategy, data, architecture)
- `prompts/` versioned prompt library (build + runtime)

# Portal text: MCP usage (build provenance)

## MCP servers (name, purpose)
Built by us (4, all read-only)
- happygut-foodgraph: the food knowledge graph (dishes → ingredients → components → cited Rule Cards)
- happygut-guidelines: the 25 cited Rule Cards, with each paper and its exact sentence
- happygut-evals: measured evaluation results and the red-flag check, for coding agents
- happygut-journal: one patient's own records, using that patient's own sign-in

Used
- GitHub MCP: pull requests, CI results and merges for each build step

## Tools exposed via MCP (our servers, 12 tools)
- foodgraph: `search_dish`, `get_components`, `explain_verdict_path`
- guidelines: `search_rules`, `get_rule`, `list_sources`
- evals: `get_results`, `pattern_recovery`, `check_red_flags`
- journal: `get_overview`, `get_recent_days`, `get_patterns`

## Permissions granted to MCP tools
- All 12 tools we built are marked read-only; knowledge changes go only through reviewed seed files in pull requests
- foodgraph / guidelines / evals: knowledge and results only; no patient data
- journal: only the records of the patient whose sign-in token it uses
- Streamable HTTP mode requires a bearer token (`MCP_BEARER_TOKEN`); stdio for local use
- GitHub MCP: scoped to the HappyGut repository; merges only after every check passes
- Claude Code asks for approval before write or execute actions, according to the session's permission mode
