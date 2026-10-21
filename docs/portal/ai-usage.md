# Portal text: AI detail usage (prototype, Oct 31)

> Paste-ready lists. Same rule as the data section: list only what's really used. Exact model versions are pinned after the Step 2 benchmark. Write the version names you actually run; don't copy placeholder names.

## Prompt usage

**Design**
- Prompts are versioned files in `prompts/runtime/` (id, version, model, temperature, output schema, last eval score)
- Every LLM call logs its prompt ID + version (Langfuse); every verdict stores the prompt version that explained it
- One prompt per agent task:
  - perception (photo → dishes)
  - dish resolver
  - evidence explainer
  - meal planner
  - red-flag checker
  - Rule Card extractor
  - contextual chunk header
  - evaluation judge
- Role prompting with hard boundaries: "clinical nutrition evidence explainer". Never says "safe", never diagnoses, never gives medication advice
- Structured outputs: every prompt returns JSON matching a Pydantic schema; invalid output is retried with the validation error fed back (Instructor)
- Few-shot: 3–5 curated examples per task (mixed Bangladeshi plate, Bangla label, Banglish text, blurry photo → ⚪ "Not sure")
- Grounded generation: the explainer only sees evidence objects with IDs, must cite an ID for every claim, and must say so when evidence is insufficient
- Quote-then-answer: extraction prompts copy the exact source sentence before producing a Rule Card (reduces hallucination)
- Minimal chain-of-thought: the verdict logic lives in the deterministic engine, so prompts don't need long reasoning. Faster and cheaper, with nothing hidden in model reasoning
- Bangla-first output: a medical-term glossary in the prompt keeps terminology consistent; plain language, ≤ 60 words, with an expandable "more"
- Layered safety: red-flag pre-check → guardrailed system prompt → post-output validator (bans "safe" and medication wording, checks every claim has a citation)

**Iteration and versioning**
- Eval-driven: every prompt change runs against the evaluation sets (promptfoo + Ragas) and is merged only if nothing regresses
- Failure cases found in testing become new few-shot examples or test cases
- Prompt versions compared side by side in Langfuse
- Build prompts (Claude Code sessions) kept in the prompt library `prompts/build/` with CLAUDE.md as project memory

## Token optimization

- Deterministic verdict engine: the decision needs no LLM, so a scan costs ~2 LLM calls (perception + explanation)
- LiteLLM router: cheap/fast model for routing and classification, stronger model only for vision and explanations; automatic fallback across providers when a free-tier quota runs out
- Caching: perception results by image SHA-256
- Caching: explanations by (dish, profile version, language); common dishes cost no new tokens
- Gemini implicit context caching: static prefix first (system prompt + glossary + few-shots), variable content last
- Compact evidence packets: top-5 reranked chunks reduced to short fact lines with IDs (~300 tokens) instead of raw documents
- Images downscaled to ≤ 1024 px before the vision model
- Local models (Ollama) handle high-volume, low-value work: PII scrubbing, Bangla normalisation, classification. Zero API tokens
- Batch jobs on the local GPU: Rule Card extraction, dish enrichment, contextual chunk headers are computed once at ingestion, never per query
- Semantic dedup: duplicate chunks removed by content hash before embedding
- Stateless calls, no chat history; weekly summaries are written from SQL-computed statistics, not raw logs
- Output caps: max_tokens per task, short answers with "more" on demand
- Streaming (SSE) for faster perceived response
- Token usage per call tracked in Langfuse

## Token optimization tools and methods (tick)
- ✅ Gemini Context Caching (implicit caching of the static prompt prefix)
- ✅ Structured outputs / JSON mode
- ✅ Cheap-model routing (LiteLLM)
- ✅ Request batching (offline enrichment and embedding jobs)
- ✅ Semantic chunk dedup
- ❌ Anthropic / OpenAI / DeepSeek caching (we don't call those APIs at runtime)
- ❌ LLMLingua, Graphify, Caveman, Codeburn, rolling summary, sliding window, KV-cache reuse, speculative decoding (not used)

## LLMs / models used (tick; +3 each, max 15)
- ✅ Claude
- ✅ Gemini
- ✅ Llama
- ✅ Qwen
- ✅ *Add:* Gemma
- ❌ ChatGPT, Kimi, DeepSeek, Mistral, Grok (not used; tick ChatGPT only if the team really uses it)

## How and why we use these LLMs
- Claude (via Claude Code): development only: architecture docs, code generation, refactoring, tests, reviews; project memory in CLAUDE.md. Not called at runtime (no free API tier)
- Gemini Flash (free tier): primary runtime model
  - meal/label photo → dishes JSON
  - Bangla/English evidence explanations
  - meal plans
  - weekly summaries
  - Why: strong vision + Bangla, JSON-schema output, free tier
- Llama (via Groq free tier): low-latency tasks
  - text-input intent routing
  - second check on red-flag free text
  - fallback explainer when the Gemini quota runs out
  - Also run locally (Llama 3.2 3B) as the offline router / red-flag fallback
  - Why: very fast inference, separate quota
- Gemma (local, Ollama, Gemma 3 4B Q4_K_M): privacy and local tasks
  - PII scrubbing (raw text never leaves our machine)
  - Bangla/Banglish normalisation
  - local vision fallback
  - Why: open weights, strong multilingual, fits 12 GB VRAM
- Qwen (local, Ollama, ~7–8B quantized): offline batch knowledge work
  - Rule Card extraction
  - dish enrichment
  - contextual chunk headers
  - synthetic Bangla/Banglish evaluation sets
  - Why: strong structured output, free unlimited batch runs
- DeepSeek-R1-Distill-Qwen-7B (local): LLM-as-judge for evaluation (claim-vs-evidence support checks), a different model from the Gemini generator to reduce self-bias
- Supporting (non-LLM) models: BGE-M3 multilingual embeddings, bge-reranker-v2-m3 cross-encoder
- Privacy note: free-tier cloud APIs may use submitted data to improve the provider's services, so only food photos and de-identified text are sent; production moves to paid tiers with no-training terms

## Retrieval & RAG (tick)
- ✅ Contextual RAG (Anthropic-style context per chunk)
- ✅ Variable / Semantic Chunking
- ✅ Graph RAG
- ✅ Knowledge Graph / Other Graph Methods
- ✅ Hybrid Search (Keyword + Vector)
- ✅ Rerankers (BGE)
- ➖ True but not ticked (no extra points): Naive RAG, Vector Database (pgvector), Query Rewriting
- ❌ Late Chunking, Agentic RAG, Self-RAG, Corrective RAG, HyDE (not used as named techniques)

## RAG architecture details
**Two retrieval paths, fused into one evidence packet**

Graph path (food facts and personal history)
- Dish resolution: Banglish → Bangla → canonical dish ID (pg_trgm + BGE-M3 name embeddings)
- Neo4j traversal: Dish → Ingredient → Component (level per 100 g)
- Rule Cards matching (component, phenotype, disease state) → cited Papers
- Patient REACTS_TO edges (personal evidence) + GENTLER_ALTERNATIVE dishes

Text path (guideline passages for the explanation)
- Corpus: CC-licensed ESPEN / IOIBD / AGA guideline text, published FODMAP composition papers, Rule Card texts
- Parsing: Docling, structure-aware (sections, headings; tables kept whole)
- Variable chunking: split by section first, then semantic breakpoints (embedding-similarity drops) into ~200–500-token chunks
- Contextual RAG: local Qwen writes a 50–100-token context header per chunk (document, section, population, recommendation strength), prepended before embedding and keyword indexing; generated once at ingestion
- Embeddings: BGE-M3, 1024-d, multilingual (Bangla queries match English guidelines)
- Index: pgvector HNSW (cosine, m=16, ef_construction=64)
- Keyword search: Postgres tsvector (English) + pg_trgm (Bangla/Banglish)
- Metadata filters: licence, phenotype, disease state, document type
- Query: built from structured facts (component + phenotype + state), not raw user text
- Hybrid fusion: Reciprocal Rank Fusion, top 50 → bge-reranker-v2-m3 → top 5

Evidence gate and grounding
- Low reranker score or no matching Rule Card → no explanation from weak evidence → ⚪ "Not sure" + a clarifying question
- Evidence packet = IDs + short fact lines (~300 tokens) → the explainer must cite IDs → a validator checks every cited ID was in the packet

Evaluation
- Recall@5, MRR on the guideline Q&A set
- Ragas faithfulness and context precision
- Ablation table: naive vector → + contextual headers → + hybrid → + reranker

## MCP usage
> **Status: PLANNED.** Fill in the portal only for servers that run by Oct 31. Repo/deploy URLs and "# endpoints actually called" come from the real build.

### Built
**happygut-foodgraph** · tick "Reused across multiple projects / clients"
- # tools: 3
- Transport: stdio, Streamable HTTP
- Language / SDK: Python, MCP Python SDK (FastMCP)
- Repo / deploy URL: GitHub repo path `mcp/foodgraph` + Tailscale Funnel URL *(after build)*
- Purpose: exposes the HappyGut Food Knowledge Graph (Bangladeshi dishes → ingredients → gut-relevant components → cited IBD Rule Cards) as read-only tools, so the app's agent, our dev tools and clinicians' AI clients share one trusted source of food evidence instead of duplicating graph queries. No patient data.
- Tools:
  - `search_dish(query, lang)`: Bangla/English/Banglish name → canonical dishes
  - `get_components(dish_id)`: ingredients, component levels, sources
  - `explain_verdict_path(dish_id, phenotype, state)`: graph path dish → component → Rule Card → paper

**happygut-journal** · tick reuse
- # tools: 3
- Transport: Streamable HTTP
- Language / SDK: Python, FastMCP
- Purpose: lets a clinician's AI client read one patient's consented, read-only summary before a visit; bearer token per clinician, scoped to patients who shared via QR
- Tools:
  - `get_symptom_trend(patient_ref, days)`
  - `get_adherence(patient_ref, days)`
  - `get_previsit_summary(patient_ref)`

**happygut-guidelines** · tick reuse
- # tools: 3
- Transport: stdio, Streamable HTTP
- Language / SDK: Python, FastMCP
- Purpose: exposes our hybrid guideline RAG (contextual chunks + Rule Cards, reranked, with citations) so the explainer agent, Claude Code and clinicians' AI clients search the same cited IBD nutrition evidence
- Tools:
  - `search_guidelines(query, phenotype, state, lang)`: top cited passages
  - `get_rule_card(id)`: structured rule + source quote
  - `cite_source(id)`: full reference (DOI / PMID, licence)

**happygut-evals** · tick reuse
- # tools: 3 (+ MCP resources for evaluation reports)
- Transport: stdio
- Language / SDK: Python, FastMCP
- Purpose: makes the evaluation harness available to coding agents, so Claude Code checks quality before and after every change (eval-driven development); also feeds live metrics to /docs
- Tools:
  - `run_eval_suite(suite)`: verdict / red-flag / RAG / trigger-recovery suites
  - `get_latest_metrics()`
  - `compare_runs(run_a, run_b)`: regression diff

**happygut-research** · tick reuse
- # tools: 2
- Transport: Streamable HTTP
- Language / SDK: Python, FastMCP
- Purpose: aggregated trigger statistics for researchers, with small groups suppressed (k ≥ 10); runs on the clearly labelled simulated cohort until real consented data exists
- Tools:
  - `get_trigger_stats(component, region)`
  - `list_cohorts()`

### Used
**Supabase MCP**
- Source: Supabase (official)
- # endpoints called: ~4
- Capabilities: tools `list_tables`, `execute_sql`, `get_advisors`, `generate_typescript_types` (server run in read-only mode)
- How: Claude Code inspected the schema, checked row-level security with the security advisors, and generated TypeScript types. Schema changes go through reviewed migration files applied with the Supabase CLI, not through MCP

**Neo4j Cypher MCP** (`mcp-neo4j-cypher`)
- Source: Neo4j Labs (open source)
- # endpoints called: 2
- Capabilities: tools `get_neo4j_schema`, `read_neo4j_cypher` (write tool not used)
- How: Claude Code inspected the graph schema and found orphan nodes and unmatched ingredients; fixes go into the reviewed seed files and the graph is rebuilt from them

**Filesystem MCP**
- Source: Model Context Protocol reference servers (open source)
- # endpoints called: ~3
- Capabilities: tools `list_directory`, `read_text_file`, `search_files`
- How: Claude Code browsed raw/bronze data-lake folders during parser and ingestion work

**GitHub MCP** (`github-mcp-server`)
- Source: GitHub (official)
- # endpoints called: ~4
- Capabilities: tools `issue_write` / `list_issues`, `create_pull_request`, `pull_request_read`, `get_file_contents`
- How: Claude Code tracked each build step as a GitHub issue, opened one pull request per step, and read PR diffs and review comments while fixing them

**Playwright MCP**
- Source: Microsoft (open source)
- # endpoints called: ~4
- Capabilities: tools `browser_navigate`, `browser_click`, `browser_file_upload`, `browser_take_screenshot`
- How: Claude Code ran end-to-end checks of the PWA hero flow (upload meal photo → verdict card in Bangla) on mobile viewport sizes and captured screenshots for the demo and /docs

### MCP clients / hosts
- Claude Code: development, schema work, graph curation
- HappyGut meal-check agent: LangGraph via `langchain-mcp-adapters` → `happygut-foodgraph`
- Claude Desktop: demo of exploring the food graph / clinician summary

### Transports
- ✅ stdio
- ✅ Streamable HTTP
- ❌ SSE (legacy), WebSocket

### Reuse, architecture and integration notes
- One foodgraph server serves the app agent, Claude Code curation and the Claude Desktop demo, so there's a single source of graph logic
- All built tools are read-only; writes go only through the reviewed ingestion pipeline
- Data separation: food knowledge (foodgraph) vs consented patient data (journal); research gets aggregates only
- Auth: bearer tokens on Streamable HTTP, published through Tailscale Funnel behind an API-key gateway; stdio local only
- Rate limits: per-token limits in the server and the gateway
- Observability: every tool call traced in Langfuse (tool, latency, caller)
- Typed contracts: Pydantic input/output models generate the tool JSON schemas

### Anything else about MCP
- Design choice: MCP for knowledge access, but the verdict engine itself stays in-process (deterministic, unit-tested), so the same decision logic isn't spread across tools
- Gotcha planned for: free quick-tunnel URLs change on restart, so we use Tailscale Funnel's stable `*.ts.net` address (free, no domain needed)
- Next: `happygut-research` (aggregated, privacy-protected trigger statistics for researchers), plus MCP resources for Rule Cards and the prompt library

## Open-source tools & libraries (AI)
- LangGraph: agent graph for the meal-check flow, dietitian loop and background jobs
- Pydantic-AI: typed agent nodes (perception, resolver, explainer, dietitian) inside the LangGraph graph
- MCP Python SDK (FastMCP) + langchain-mcp-adapters: our MCP servers and the agent's MCP tool calls
- LiteLLM: one client across Gemini, Groq and Ollama; model routing, fallbacks, response caching
- Ollama (llama.cpp runtime): local quantized inference on the team GPU
- Gemma, Qwen, Llama and DeepSeek-R1-Distill open-weight models: PII scrubbing, Bangla normalisation, batch knowledge extraction, offline routing, LLM-as-judge
- BGE-M3 (served by Ollama) + bge-reranker-v2-m3 (sentence-transformers): multilingual embeddings and reranking
- sentence-transformers: fine-tuning the dish-name embedding model
- pgvector + Neo4j: vector index and knowledge graph for Graph RAG
- Docling + Crawl4AI: guideline documents → structured, chunkable text
- Instructor + Pydantic: typed, validated LLM outputs with automatic retry
- Microsoft Presidio: PII detection before any cloud call
- LightGBM + scikit-learn + SHAP: flare early-warning model and explanations
- Ragas: RAG faithfulness and context metrics
- promptfoo: prompt regression tests in CI
- Langfuse: tracing, prompt versions, evaluation scores, user-feedback scores
- Streamlit: Evaluation Lab

## Agent frameworks & orchestration
**Meal-check graph (LangGraph state machine)**
1. Router: input type (photo / text) and language
2. Safety Sentinel: red-flag rules + LLM second check; can stop the graph and show the escalation screen
3. Privacy node: local Gemma + Presidio strip PII
4. Perception agent (Gemini vision): dishes, ingredients, method, portion → JSON
5. Dish Resolver agent: calls the `search_dish` MCP tool; ambiguous match → interrupt to ask the user (human-in-the-loop)
6. Evidence Retriever, two parallel branches: graph path (`explain_verdict_path` MCP tool + personal edges) and hybrid RAG
7. Verdict Engine: deterministic tool, not an LLM
8. Explainer agent (Gemini): grounded Bangla/English explanation with citations
9. Output Guard: schema, citation and banned-claim checks; retry once, otherwise a safe template

**Other agents**
- Dietitian agent: generator–critic loop. The LLM drafts a weekly plan, the verdict engine checks every dish, failing dishes are regenerated (max 2 rounds)
- Knowledge Enrichment agent: takes the "Not sure" / unmatched-dish queue, drafts graph facts, sends them to human review
- Weekly Summary agent: writes the digest from SQL-computed statistics only
- Trigger Discovery + Flare Early Warning: nightly jobs scheduled by n8n

**Patterns**
- Tool calling through MCP, with an allow-list of tools per agent
- Conditional edges, parallel branches, human-in-the-loop interrupts
- Postgres checkpointer: resumable runs
- LiteLLM retries and cross-provider fallbacks

## Fine-tuning / adaptation
- Embedding fine-tuning (planned for Oct 31): sentence-transformers contrastive training (MultipleNegativesRankingLoss) of the dish-name encoder
  - Training pairs: Banglish / Bangla / English dish names ↔ canonical dish IDs, from Dakshina transliterations, graph aliases and reviewed synthetic spellings
  - Measured by dish-resolution Recall@1 against the base model
- Adaptation without weight changes: few-shot examples of Bangladeshi dishes, a Bangla medical glossary in prompts, retrieval grounding
- Finals: QLoRA (PEFT + bitsandbytes, fits 12 GB VRAM) on a small Gemma/Qwen model for Bangla explanation style, trained on team-reviewed explanations

## Evaluation & quality measurement
**Test sets (all versioned)**
- ~200-food verdict set, labelled by the team from Rule Cards
- ~300 team meal photos with dish labels
- ~100 guideline Q&A pairs with sources
- Red-flag suite (Bangla / English / Banglish)
- Banglish dish-name set
- Simulated patient cohort

**Methods**
- Ragas: faithfulness, context precision/recall, answer relevance
- LLM-as-judge: local DeepSeek-R1-Distill-Qwen-7B (a different model from the Gemini generator) scores explanations for groundedness, clarity, Bangla fluency and tone against a rubric; checked against human labels on 50 samples (Cohen's kappa reported)
- Human evaluation: native Bangla speakers on the team blind-rate 50 explanations (readability, accuracy)
- Ablations: naive RAG → contextual → hybrid → reranker
- Verdict engine vs LLM-only baseline, compared with McNemar's test
- Regression gate: promptfoo suite runs in CI on every prompt or model change; merge blocked if red-flag recall < 100% or verdict accuracy drops > 2 points
- Online signals: "was this right for you?" feedback logged as Langfuse scores; latency and token cost per call
- Bootstrap 95% confidence intervals; slices by language, sex and phenotype

## Guardrails, safety & privacy
**Input**
- Red-flag Safety Sentinel runs first (rules + LLM second check) → escalation screen, no diet advice
- PII scrubbing: Presidio + local Gemma (Bangla names, +8801 phone numbers, NID numbers, addresses) before any cloud call
- EXIF/GPS stripped from photos; "photograph the food, not people" hint
- Non-food image → rejected
- Prompt-injection defence: text read from labels/menus is treated as data inside delimiters, never as instructions
- Tools are read-only and allow-listed per agent; Cypher is parameterised
- Scope guard: diagnosis or medication questions → polite refusal + "ask your doctor"

**Output**
- Pydantic schema validation; retry once, otherwise a safe template
- The LLM can't change the verdict: the validator checks the explanation matches the engine's verdict
- Citation check: every claim must cite an evidence ID that was retrieved; unsupported claims dropped → ⚪ "Not sure"
- Banned-claim filter (Bangla + English): "safe", "cure", dose or medication-change wording
- Stricturing Crohn's hard rules applied before any LLM output
- Low confidence → ⚪ "Not sure" or a clarifying question

**Privacy and accountability**
- Consent scopes, row-level security, pseudonymous IDs
- Free-tier cloud APIs receive only food photos and de-identified text
- Every verdict logs its evidence IDs + model and prompt versions
- "Not a medical device" disclaimer

## Frontend AI / visual app builders
> Tick only the tools the team really uses during the build.

**Tick**
- ✅ Lovable: initial PWA shell and hero-flow screens
- ✅ v0 (Vercel): individual components
- ✅ Claude Artifacts: interactive prototypes and layout exploration
- ✅ Gemini Canvas: Bangla UI copy drafts
- ✅ *Add:* Google Stitch: screen designs exported to Figma (*check it's still available when you start*)

**How we used them**
- Lovable: generated the first React + Tailwind + shadcn/ui + Supabase app (scan screen, verdict card, daily check-in, My Gut dashboard), synced to GitHub, then continued in Claude Code
- v0: generated self-contained components (verdict card with evidence bar, trigger-insight card, Recharts trend charts, flare-risk gauge), added to the codebase with the shadcn CLI
- Claude Artifacts: quick clickable prototypes to compare verdict-card variants and the clinician pre-visit report layout before building
- Gemini Canvas: first drafts of bilingual UI copy, which native Bangla speakers on the team then reviewed and edited
- Google Stitch → Figma: hero-flow screen designs for the Figma link and design review

**Share AI-built:** target ~80% of UI code AI-generated, then refined by hand; the actual share is reported from git history at submission

**Human-owned parts**
- Bangla typography and line breaking
- Safety wording (verdicts, red-flag screen, disclaimer)
- Accessibility fixes
- Final Bangla copy

**Custom workflow**
- Shared design tokens (colours, verdict palette, spacing) given to every tool, so generated pieces match
- Every generated string moved into `bn` / `en` message files (i18n); no hard-coded text
- Noto Sans Bengali / Hind Siliguri fonts; Bangla numerals optional
- Checks on every UI change: axe + Lighthouse (accessibility, performance) and a mobile low-bandwidth budget (small initial JavaScript bundle, lazy-loaded charts)
- UI-generation prompts saved in the prompt library (`prompts/build/`)

## Workflow automation
**Tick (4 = max, + n8n bonus)**
- ✅ n8n (self-hosted)
- ✅ LangGraph
- ✅ *Add:* GitHub Actions
- ✅ *Add:* Supabase Database Webhooks

**Automated workflows**

n8n
- Reminders: per-user cron (Asia/Dhaka) → Supabase query → Bangla/English Web Push for doses and check-ins
- Nightly intelligence (02:00): runs Trigger Discovery + Flare Early Warning (FastAPI) → updates Personal Gut Graph edges
- Nightly alerts: push "rising flare risk" with top factors, and "new trigger found" insights
- Weekly digest (Sunday): Weekly Summary agent writes a Bangla/English digest from SQL-computed statistics → push + in-app card
- Weekly clinician report: pre-visit PDF (WeasyPrint) → signed expiring link
- Knowledge ingestion: Supabase Storage upload webhook → parse → chunk → contextual headers (local Qwen) → embed (BGE-M3) → Rule Card candidates → review-queue notice
- Knowledge-gap loop (daily): collects ⚪ "Not sure" / unmatched dishes → Knowledge Enrichment agent drafts graph facts → human review
- Error workflow: any failed run → team chat webhook alert

LangGraph
- Real-time meal-check agent graph (Safety Sentinel → privacy → perception → dish resolver → evidence retrieval → verdict engine → explainer → output guard)
- Dietitian generator–critic loop

Supabase Database Webhooks
- New meal check / check-in → FastAPI → red-flag check + incremental trigger update in real time

GitHub Actions
- On any PR changing prompts, models or retrieval: run the promptfoo + Ragas evaluation suite and red-flag tests
- Block the merge on regression; post an eval summary comment on the PR

## Local / on-device LLMs
**Runtimes**
- ✅ Ollama: serves all local LLMs (GGUF)
- ✅ *Add:* Hugging Face Transformers / sentence-transformers (PyTorch, CPU): bge-reranker cross-encoder, embedding fine-tune
- ➕ LM Studio: tick only if the team really uses it to benchmark models side by side

**Local models we actually run** (tick the exact versions you run)
- ✅ Gemma 3 4B (*add*): online PII scrubbing, Bangla/Banglish normalisation, local vision fallback
- ✅ Qwen 2.5 7B Instruct: nightly batch work (Rule Card extraction, dish enrichment, contextual chunk headers, synthetic Bangla eval sets)
- ✅ Llama 3.2 3B: always-on offline router and red-flag second check when the Groq quota runs out
- ✅ DeepSeek-R1-Distill-Qwen-7B (*add*): LLM-as-judge (does the evidence support each claim?)

**Hardware, quantization, why local**
- GPU: AMD Radeon RX 7700 XT, 12 GB VRAM, ROCm on Ubuntu (Ollama ROCm build) · 16 GB system RAM
- Format: GGUF, Q4_K_M quantization, 8k context
- Online set (always loaded, ~7–8 GB): Gemma 3 4B + Llama 3.2 3B + BGE-M3 on the GPU; reranker on the CPU
- Batch set (swapped in at night): Qwen 2.5 7B, DeepSeek-R1-Distill 7B (~5 GB each)
- Models capped at ≤ 7B per slot, because 16 GB RAM leaves no room for CPU offload of larger models
- Ollama settings: `OLLAMA_MAX_LOADED_MODELS=3`, `keep_alive` long for online models, short for batch models
- Reached by the hosted backend through Tailscale Funnel (API-key gateway)
- Why local, privacy: raw text that may contain PII never leaves our machine; cloud models only see de-identified text
- Why local, cost: $0, with no rate limits for batch jobs over thousands of chunks
- Why local, resilience: automatic fallback when free-tier cloud quotas run out
- Why local, sovereignty: inference runs on team hardware in Bangladesh
- Why local, roadmap: the same small models are candidates for the offline/on-device app

## Agentic frameworks used
- ✅ LangGraph: orchestrates the meal-check graph (sentinel → privacy → perception → resolver → retrieval → verdict engine → explainer → guard), the dietitian generator–critic loop, interrupts, Postgres checkpointing
- ✅ Pydantic-AI: typed agent nodes inside the LangGraph graph (perception, dish resolver, explainer, dietitian), with typed outputs, tool calling and model-agnostic providers (Gemini, Groq, Ollama). Batch data pipelines keep using Instructor
- ➕ DSPy (optional): offline optimisation of the perception and dish-resolver prompts. Picks the best few-shot examples against our labelled photo and Banglish sets, run with local models. Tick only if done
- ✅ CrewAI: offline knowledge-curation crew for Rule Cards, run on local models
  - Researcher agent: finds passages via Europe PMC + guideline RAG
  - Extractor agent: drafts the Rule Card with an exact quote
  - Critic agent: checks the quote supports the rule
  - Output → human review queue
- ✅ smolagents: data-ops code agent (local Qwen, sandboxed). Writes and runs read-only pandas / Cypher analysis on unmatched ingredients, orphan graph nodes and evaluation failures, then proposes fixes as reviewable diffs
- ❌ AutoGen, Swarm, OpenAI Agents SDK, Letta, Mastra, Agno, Google ADK, Hermes, OpenClaw (not used)

## AI Development Lifecycle (AI-DLC)
**Frameworks adopted (3 = max)**
- ✅ GitHub Spec-Kit: spec → plan → tasks for every feature
- ✅ Claude Skills: repeatable project procedures as `.claude/skills/`
- ✅ AGENTS.md spec: cross-tool agent memory (mirrors CLAUDE.md for Cursor / Lovable / other agents)

**Process notes (phases, artifacts, review gates)**
1. Inception: strategy, data and AI design docs with decision logs (`docs/01-strategy.md`, `docs/03-data.md`, portal texts) + non-negotiable product rules in CLAUDE.md
   - Gate: team review of every decision
2. Specification (Spec-Kit): CLAUDE.md rules become the Spec-Kit constitution
   - Each feature gets `/specify` → spec.md (user stories, acceptance criteria incl. safety rules) → `/plan` → plan.md (architecture, contracts) → `/tasks` → tasks.md
   - Features: 001 knowledge layer · 002 meal-check hero flow · 003 check-in + trigger discovery · 004 flare early warning · 005 dietitian · 006 clinician report · 007 foodgraph MCP
   - Gate: spec checked against the constitution before any code
3. Construction: Claude Code implements tasks in small PRs (one GitHub issue per task via GitHub MCP); Lovable / v0 for UI
   - Claude Skills encode repeatable steps: add-rule-card, add-dish, new-prompt-version, run-evals
   - Gate: unit tests on every verdict-engine rule
   - Gate: CI eval regression (red-flag recall 100%, verdict accuracy must not drop)
   - Gate: human review of every AI-generated PR; native-speaker review of Bangla copy
4. Operations and learning: Langfuse traces, Evaluation Lab, user feedback, knowledge-gap queue
   - Lessons feed back into the constitution, skills and prompt library
- Memory bank: CLAUDE.md + AGENTS.md (project memory), `docs/` decision logs, versioned `prompts/` library (build provenance)
- Accountability: every AI-generated change is reviewed and owned by a named team member; AI usage documented per the Congress code of conduct

## Anything else about your AI usage?
- Core design principle: "AI perceives and explains, a deterministic engine decides". Every verdict is reproducible, unit-tested and explainable, so the LLM can't invent a medical judgement
- Personal AI, not generic AI: the Personal Gut Graph learns each patient's own triggers from their logs (Bayesian N-of-1) instead of giving one-size-fits-all IBD diet rules
- Bangla-first AI: Bangla / English / Banglish input, Bangladeshi dish knowledge graph, Bangla medical glossary, native-speaker review of all generated Bangla
- Honest evaluation: results on simulated patients are always labelled as simulated; real-data claims are made only where we measured them
- Explainability everywhere: verdict evidence bar, cited sources, SHAP factors on flare alerts, graph path from dish to guideline
- Human oversight: humans approve every knowledge-graph fact the AI extracts; humans review every AI-generated PR and all safety wording
- Model and data cards: one page per model role and per dataset (purpose, limits, licence, evaluation results), published in `/docs`
- Cost-aware AI: runs at $0 on free tiers + one 12 GB GPU through caching, routing and local fallbacks, a realistic path for low-resource settings
- Privacy by architecture: local models handle anything that might contain PII; cloud models only see food photos and de-identified text
- Known limits, stated openly: not a medical device; flare prediction not yet validated on real patients; dish recognition limited to dishes in our graph (unknown → ⚪ "Not sure")
- Next: federated learning across users, QLoRA-tuned Bangla explainer, on-device small model for offline use, clinical validation with partner gastroenterologists
