# Portal text: AI detail usage (prototype, updated 20 Nov)

> Paste-ready lists for the portal's "AI Detail Usage" page. **List only what is really used.** Every line below was checked against the code on 20 Nov 2026. Unticked items are in `submission-scope.md` under "not built".

## Prompt usage
```
Versioned prompt files in prompts/runtime/ (Markdown with a header: id, version, model, temperature, output schema, changelog, eval score)
4 prompts: meal-perception (photo/text → dishes JSON), meal-explanation (the "why" in Bangla or English), g2-dish-aliases (v1 → v2, offline spelling job), g1-context-header (prepared for the guideline corpus)
Every meal check stores which perception and explanation prompt versions produced it
Role prompting with strict limits: the model only describes food or explains a verdict the engine already made; it never judges, never says "safe", never gives medicine advice
Structured JSON output validated against Pydantic schemas
```

## Token optimization
```
Deterministic verdict engine: the decision needs no LLM, so a check needs at most 2 model calls (read the plate, write the explanation)
Typed dish names are matched locally against the knowledge graph, so no perception call is needed
Small model first (Gemini flash-lite), larger model only as fallback; Groq as a second provider
Structured JSON output: no free-text parsing, fewer retries
If no model is available, a template explanation is shown, so a check never fails
```

## Token optimization tools and methods (tick)
- ✅ Structured outputs / JSON mode
- ✅ Cheap-model routing
- ❌ Not used: context caching, semantic chunk dedup, request batching, prompt compression, KV-cache reuse

## LLMs / models used (tick)
- ✅ Claude (development, Claude Code; LLM judge for knowledge review)
- ✅ Gemini (runtime)
- ✅ Gemma (offline spelling job, Gemma 3 12B)
- ⚠️ Llama: only as a backup in the Groq fallback list
- Add: `gpt-oss-120b (via Groq)`, optionally `BGE-M3 (embeddings)`
- ❌ Not used: Qwen, DeepSeek, ChatGPT, Mistral, Kimi, Grok

## How and why we use these LLMs
```
Claude (via Claude Code): development only: architecture, code, tests, reviews, documentation; LLM judge for the knowledge review
Gemini Flash / Flash-Lite (free tier, Google AI Studio): runtime: reads meal photos and text into dishes JSON; writes the Bangla or English explanation
gpt-oss-120b on Groq (free tier): fallback for explanations when Gemini's quota runs out; Llama models on Groq as further backups
Gemma 3 12B (Ollama, team GPU): offline job suggesting dish-name spellings, each checked by an LLM judge
BGE-M3: offline dish-name embeddings (not used by the live app yet)
```

## Retrieval & RAG (tick)
- ✅ Knowledge Graph / other graph methods
- ✅ Graph RAG (with the wording below)
- ❌ Not used: naive / contextual RAG, semantic or late chunking, vector database, hybrid search, rerankers, agentic / self / corrective RAG, query rewriting

## RAG architecture details
```
Graph-based retrieval: each dish is resolved by fuzzy matching over Bangla, English and English-letter names in the knowledge graph (109 dishes)
Path: dish → ingredients → gut-relevant components (levels) → Rule Cards for this patient's diagnosis and state → the exact quoted sentence and DOI/PMID
That retrieved path is given to the explanation model, which may only explain it; a check compares its text with the engine's verdict
No evidence → ⚪ "Not sure"
Planned: vector search over guideline text (pgvector, BGE-M3), once the corpus is licensed and loaded
```

## MCP usage

### Built (4 servers, 3 tools each, all read-only, Python MCP SDK)
| Server | Transport | Tools | Purpose |
|---|---|---|---|
| happygut-foodgraph | stdio, Streamable HTTP | search_dish, get_components, explain_verdict_path | Food knowledge graph as read-only tools: dishes → ingredients → gut-relevant components → cited Rule Cards. No patient data |
| happygut-guidelines | stdio, Streamable HTTP | search_rules, get_rule, list_sources | The 25 cited Rule Cards: search by food or component, read a rule with its exact quoted sentence and DOI/PMID, list the sources and licences |
| happygut-evals | stdio, Streamable HTTP | get_results, pattern_recovery, check_red_flags | Measured evaluation results and the red-flag check as tools, so a coding agent can check quality before and after a change |
| happygut-journal | stdio, Streamable HTTP | get_overview, get_recent_days, get_patterns | One patient's own records, read-only, using that patient's own sign-in; for a patient's AI assistant or a pre-visit summary |

"Reused across multiple projects": not ticked.

### Used
| Server | Tools used | What for |
|---|---|---|
| GitHub MCP | create_pull_request, pull_request_read, list_pull_requests, merge_pull_request | Claude Code opened one pull request per step, read CI results and merged after checks passed |

Tick Supabase MCP only if a teammate really connected it (read-only; migrations are written as files). Neo4j, Filesystem and Playwright MCP were not used.

### MCP clients / hosts
`Claude Code, Claude Desktop`

### Transports
stdio ✅, Streamable HTTP ✅ (behind a bearer token)

### Reuse, architecture and integration notes
```
4 read-only servers built with the MCP Python SDK; every tool is marked read-only
Knowledge (foodgraph, guidelines) is kept separate from patient data (journal); journal only sees the records of the patient whose sign-in it uses
stdio for local use; Streamable HTTP requires a bearer token
```

### Anything else about MCP
```
The verdict engine stays in-process (deterministic, unit-tested); MCP is for knowledge access only
Next: a research server with aggregated, privacy-protected statistics once consented data exists
```

## Open-source tools & libraries (AI)
```
LangGraph: the meal-check flow as a state graph
Pydantic-AI + Pydantic v2: model calls with typed, validated outputs
MCP Python SDK: our 4 MCP servers
Presidio + spaCy: PII detection
LightGBM: flare-risk model with SHAP explanations
Ollama: offline GPU jobs (Gemma 3 12B); sentence-transformers with BGE-M3
FastAPI, React, Vite, Tailwind, Recharts, Zod, react-i18next
n8n: scheduled workflows; Playwright: end-to-end checks and screenshots
```

## Agent frameworks & orchestration
```
Meal-check graph (LangGraph state machine):
red-flag sentinel (rules, English/Bangla/romanised) → escalation screen, no diet advice
→ PII scrub → perception (Gemini, structured JSON) → dish resolver (knowledge graph)
→ deterministic verdict engine (stricture rules first) → explanation agent (Gemini / Groq)
→ guard checks the explanation against the verdict; on mismatch a template is shown
Each step streams to the phone over Server-Sent Events
```

## Fine-tuning / adaptation
```
No fine-tuning. Adaptation is prompt-level (versioned prompts, structured output) plus retrieval of cited Rule Cards and each patient's own diary patterns.
```

## Evaluation & quality measurement
```
Reproducible evaluation run (no language model): evals/RESULTS.md
• Pattern Finder on 200 simulated patients: found 274 of 400 hidden contributors (68%)
• Red-flag suite (team-written): 29 of 29 emergency phrases caught, 0 of 30 false alarms
• Verdict engine: 763 of 763 verdicts identical on repeat; every warning cites a Rule Card; stricture rule 19 of 19
• Dish names: every Bangla, English and alternative spelling resolves to its own dish
• Flare-risk model: ROC AUC 0.658 vs 0.558 for the rule-based score, on held-out simulated patients
LLM judge reviewed every dish, Rule Card and Bangla string against published sources (not clinical review)
Tests on every pull request (GitHub Actions)
Not yet measured: photo recognition, agreement with a dietitian, real patients
```

## Guardrails, safety & privacy
```
Input
• Red-flag sentinel runs first, on the raw text (rules in English, Bangla and romanised Bangla) → escalation screen, no diet advice
• PII scrub before any cloud AI call: Bangladesh rules (names after self-introduction, +880 phones, NID/birth numbers, emails, URLs) + Presidio
• Photos: type and size checks, downscaled, EXIF/GPS removed
Output
• The engine decides; the LLM only explains, and a guard checks that its text matches the verdict, otherwise a template is shown
• Never "safe" (graded verdicts only); patterns are "linked to", never "caused", and need ≥3 occurrences
• No evidence → ⚪ "Not sure"; never any advice to start, stop or change a medicine
```

## Frontend AI / visual app builders
- ✅ Add **Claude Code**
- Tick Lovable, v0, Claude Artifacts, Gemini Canvas or Google Stitch only if a teammate really used one (the git history has no Lovable commits)
```
Claude Code: built and redesigned the React + Tailwind PWA (meal check, verdict card, nightly diary, My Gut, patterns, doctor's report, live /docs page), checked with Playwright screenshots at phone sizes
```

## Workflow automation
- ✅ n8n (4 workflows in `n8n/workflows`: health check, nightly refresh, weekly safety self-check, failure alert email)
- ✅ LangGraph
- ✅ GitHub Actions, if listed

## Local / on-device LLMs
- Runtimes: ✅ Ollama, ✅ sentence-transformers (✅ Hugging Face Transformers underneath)
- Models: ✅ `Gemma 3 12B`, ✅ `BGE-M3 (embeddings)`; ❌ Llama, Qwen, DeepSeek were not run locally
```
GPU: AMD Radeon RX 7700 XT (12 GB VRAM) on Ubuntu, PyTorch on ROCm. The GPU machine is never a server: it runs finite jobs and exchanges files with the team's Windows machines through git
Job G2, dish-name spellings: Gemma 3 12B on Ollama (model digest recorded), versioned prompt g2-dish-aliases v2, temperature 0.7, 3 samples with fixed seeds, a spelling kept only if 2 of 3 samples agree; 61 dishes in 165 s → 137 candidates, of which an LLM judge accepted 50 and rejected 87
Job G3, embeddings: BAAI/BGE-M3 with sentence-transformers, 302 dish names → 1024-dimension normalised vectors in 0.8 s
Every job writes meta.json (model, digest, git commit, prompt version, seeds, timings) and its output to data/gpu_jobs/, so runs are reproducible and reviewable in pull requests
Why local: $0 cost, no data leaves the team, fixed model versions; the live app does not depend on the GPU
```

## Agentic frameworks used
- ✅ LangGraph, ✅ Pydantic-AI
- ❌ Not used: CrewAI, smolagents, DSPy, AutoGen and the rest

## AI Development Lifecycle (AI-DLC)
- ✅ GitHub Spec-Kit, ✅ Claude Skills, ✅ AGENTS.md
```
Inception: strategy, architecture and data docs with decision logs (docs/); non-negotiable product rules in a constitution and AGENTS.md / CLAUDE.md
Specification (Spec-Kit): one spec per feature (specs/001 knowledge layer, 002 meal check, 003 personal layer) with requirements, plan and tasks
Build: Claude Code works from the specs; project skills for repeatable jobs (add a dish, add a Rule Card, new prompt version, run evaluations)
Gate: one pull request per step; it merges only when CI passes (engine, backend, MCP servers, seeds, web app, database tests) and the secret scan is clean
Review: every dish, Rule Card and Bangla string reviewed by an LLM judge against published sources (not clinical review)
Measure: deterministic evaluation run after changes (evals/RESULTS.md), numbers copied into the app and the submission
```

## /docs module
✅ Built: https://happygut-web.vercel.app/docs (pitch deck + technical documentation with live data; admin page at `/docs/admin` to switch it on or off, schedule it and edit text, order and team).

## Anything else about your AI usage?
```
Core principle: "AI perceives and explains, a deterministic engine decides". Every verdict is reproducible (763 of 763 identical on repeat), unit-tested and explainable, so the LLM can't invent a medical judgement.
Personal AI, not generic AI: the Flare Pattern Finder (Bayesian N-of-1) learns which foods and habits are linked to each patient's own worse days, and a LightGBM model with SHAP drivers adds an early flare estimate. Both are trained and evaluated on simulated patients only.
Safety before intelligence: red flags stop all food advice before any model runs; personal details are removed before any cloud AI call.
Bangla first: every screen, verdict and explanation in Bangla and English.
See it live, no sign-in needed: https://happygut-web.vercel.app/docs (pitch deck and technical documentation) and /about (how it works).
```
