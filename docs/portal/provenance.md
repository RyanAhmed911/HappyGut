# Portal text: Data & AI provenance (required field)

## Data sources
- Internal: Supabase app database (profiles, meal checks, verdicts, HBI/SCCAI check-ins, adherence, verdict feedback), Neo4j Personal Gut Graph, team-authored Rule Cards
- Free APIs: USDA FoodData Central (CC0), Open Food Facts (ODbL), Europe PMC (licence-filtered open access), PubMed E-utilities (citation metadata)
- Scraped / crawled: Wikipedia Bangladeshi cuisine pages, English + Bangla (CC BY-SA); open-access ESPEN, IOIBD and AGA guideline documents
- Open datasets: Food Composition Table for Bangladesh (INFS, University of Dhaka), Wikidata (CC0), published FODMAP composition tables, Google Dakshina (CC BY-SA)
- User uploads: meal / menu / label photos; ~300 team-captured Bangladeshi meal photos (test set)
- Synthetic (always labelled): simulated IBD patient cohort with injected triggers; generated Bangla/Banglish, red-flag and guideline Q&A evaluation sets
- Not used: proprietary databases (e.g. Monash FODMAP), social-media health posts, real patient records

## AI models
- Gemini Flash (free tier): meal / label vision, Bangla/English explanations, meal plans, weekly summaries
- Llama (Groq free tier): fast routing, red-flag second check, fallback explainer; local Llama 3.2 3B for synthetic test utterances (batch)
- Gemma 3 4B (local, batch): Bangla/Banglish dish-name variants and Bangla draft strings
- Qwen 2.5 7B (local, batch): Rule Card and dish enrichment drafts, contextual chunk headers
- DeepSeek-R1-Distill-Qwen-7B (local, batch): LLM-as-judge for the evaluation run
- BGE-M3 (fine-tuned for dish names) + bge-reranker-v2-m3 + Bengali NER: embeddings, reranking, PII detection (CPU)
- Custom models: LightGBM flare early-warning model (+ SHAP); Bayesian N-of-1 trigger model
- Claude (via Claude Code): development only, not at runtime

## Responsible AI
- The LLM never decides: verdicts come from a deterministic, unit-tested engine; AI only reads inputs and explains
- Graded verdicts, never "safe"; ⚪ "Not sure" when evidence is weak; every claim cites a source
- Red-flag symptoms stop diet advice and direct the user to a doctor or emergency care; no medication advice, ever
- Stricturing Crohn's safety rules applied before any AI output
- Privacy: PII stripped inside our backend (Presidio + Bangladesh rules + Bengali NER) before any cloud call; EXIF/GPS removed; pseudonymous IDs; consent scopes; row-level security; export and delete on request
- Free-tier cloud APIs only receive food photos and de-identified text
- Bias checks: metrics broken down by language (Bangla / English / Banglish), sex and disease phenotype; native-speaker review of Bangla output
- Transparency: evidence bar, citations, SHAP factors on alerts, model/data cards, prompt and model versions logged per verdict
- Honesty: simulated-data results always labelled; no fabricated traction or outcomes
- Human oversight: humans approve AI-extracted knowledge and review every AI-generated code change
- Legally sourced data only, each source's licence recorded; positioned as self-management support, not a medical device

# Portal text: Tooling & IDE

## IDE / Editor
- VS Code + Claude Code (main AI coding agent)
- Lovable and v0 for UI generation; Claude Artifacts for prototypes

## Deployment method
- Frontend PWA: Vercel (free)
- Backend API: FastAPI in Docker on Hugging Face Spaces (free CPU tier, no card)
- Team GPU (AMD RX 7700 XT): Ollama for one-off batch sessions only; nothing live runs on it
- n8n and the MCP servers: on Hugging Face Spaces alongside the backend
- Managed data: Supabase (Postgres + pgvector + Auth + Storage, Mumbai/Singapore region), Neo4j AuraDB Free
- CI/CD: GitHub Actions (tests, evaluation regression gate); Vercel preview deploys per PR

## Frameworks & libraries
- Frontend: React, Vite (PWA), Tailwind, shadcn/ui, Zod, Recharts, D3.js
- Backend: FastAPI, Pydantic, LiteLLM, Supabase client
- AI / agents: LangGraph, Pydantic-AI, Instructor, CrewAI, smolagents, MCP Python SDK (FastMCP), langchain-mcp-adapters
- Retrieval: pgvector, Neo4j, BGE-M3 + bge-reranker via sentence-transformers
- Data: Docling, Crawl4AI, Scrapy, pandas, DuckDB, Delta Lake, Pandera, Presidio
- ML: LightGBM, scikit-learn, SHAP, NumPy/SciPy
- Eval / ops: Ragas, promptfoo, Langfuse, pytest, Schemathesis, Streamlit, Plotly
- Automation: n8n

## Context / memory files
- `CLAUDE.md`: project context and non-negotiable product rules
- `AGENTS.md`: the same rules for other coding agents (Cursor, Lovable, others)
- `.claude/skills/`: repeatable procedures (add-rule-card, add-dish, new-prompt-version, run-evals)
- `.specify/memory/constitution.md` + `specs/*/spec.md, plan.md, tasks.md` (Spec-Kit)
- `docs/` decision logs (strategy, data, architecture)
- `prompts/` versioned prompt library (build + runtime)
- Lovable project knowledge file (design tokens, Bangla/i18n rules)

# Portal text: MCP usage (build provenance)

## MCP servers (name, purpose)
Built by us
- happygut-foodgraph: Food Knowledge Graph (dishes → ingredients → components → cited Rule Cards)
- happygut-guidelines: hybrid guideline RAG with citations
- happygut-journal: consent-scoped patient summaries for clinicians' AI clients
- happygut-evals: evaluation harness for coding agents (eval-driven development)
- happygut-research: aggregated, small-group-suppressed trigger statistics

Used
- Supabase MCP: schema inspection, RLS checks, TypeScript types (read-only)
- Neo4j Cypher MCP: graph inspection and curation checks (read-only)
- Filesystem MCP: raw data-lake folders during ingestion work
- GitHub MCP: issues and pull requests per build step
- Playwright MCP: end-to-end tests of the PWA hero flow, demo screenshots

## Tools exposed via MCP (our servers, 14 tools)
- foodgraph: `search_dish`, `get_components`, `explain_verdict_path`
- guidelines: `search_guidelines`, `get_rule_card`, `cite_source`
- journal: `get_symptom_trend`, `get_adherence`, `get_previsit_summary`
- evals: `run_eval_suite`, `get_latest_metrics`, `compare_runs`
- research: `get_trigger_stats`, `list_cohorts`

## Permissions granted to MCP tools
- All 14 tools we built are read-only; data changes go only through the reviewed ingestion pipeline
- foodgraph / guidelines: read-only Neo4j and Postgres roles limited to knowledge tables; no patient data
- journal: bearer token per clinician, limited to patients who shared by QR consent; revocable; every call audit-logged
- research: aggregates only, k ≥ 10 suppression; no row-level access
- evals: stdio only (local dev); runs test suites, can't modify code or data
- Remote servers (Streamable HTTP) run on the always-on backend with bearer tokens, rate limits and Langfuse tracing
- Supabase MCP: read-only mode; schema changes only through reviewed migration files (Supabase CLI); the prototype holds simulated data only
- Neo4j Cypher MCP: read tools only; fixes go into reviewed seed files and the graph is rebuilt from them
- Filesystem MCP: limited to the `data/` folder
- GitHub MCP: scoped to the HappyGut repo; no merges without human approval
- Playwright MCP: test/staging URLs only, synthetic accounts
- Claude Code asks for approval before any write or execute tool call
