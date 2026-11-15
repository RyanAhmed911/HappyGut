# Portal text: Data lifecycle (prototype, Nov 20)

> Paste-ready lists for the preliminary form. Source of truth: `docs/03-data.md` §0. Anything not listed here is a Finals item.

## 1. Data sources

**Internal**
1. Supabase app database (patient profiles, meal checks, verdicts, Harvey-Bradshaw Index and SCCAI daily check-ins, medication adherence, verdict feedback)
2. Neo4j Personal Gut Graph (learned tolerances)
3. Team-authored Rule Cards (structured IBD guidance)

**External free APIs**
1. USDA FoodData Central
2. Open Food Facts
3. Europe PMC
4. PubMed E-utilities

**Public web**
1. Wikipedia (Bangladeshi cuisine pages in English and Bangla)
2. Open-access ESPEN, IOIBD and AGA guideline documents

**Open datasets**
1. Food Composition Table for Bangladesh (INFS, University of Dhaka)
2. Wikidata
3. Published FODMAP composition tables
4. Google's Dakshina dataset

**User uploads**
1. Meal, menu and label photos
2. Team-captured set of ~300 Bangladeshi meal photos (test set)

**Synthetic data**
1. Simulated IBD patient cohort (with known injected food triggers)
2. Generated Bangla/English evaluation sets
3. Red-flag and guideline Q&A evaluation sets

## 2. Acquisition

**Scrapers / crawlers**
- Scrapy spiders: Wikipedia Bangladeshi & Bengali cuisine categories (EN + BN)
- Crawl4AI: open-access IBD guideline pages → clean markdown for RAG
- Wikidata SPARQL harvester: dishes, ingredients, Bangla labels
- Etiquette: robots.txt respected, 1 req/s throttle, identifying User-Agent, ETag caching, exponential-backoff retries
- No anti-bot evasion (no CAPTCHA/paywall bypass)
- Licence gate: every crawl job tagged with source licence; non-open content → Rule Cards only

**MCP servers for data access**
- Built: happygut-foodgraph (food KG: search_dish, get_components, explain_verdict_path)
- Used: Supabase MCP (Postgres schema & queries)
- Used: Neo4j Cypher MCP (graph queries & curation)
- Used: Filesystem MCP (raw data-lake folders)
- Transports: stdio (local), Streamable HTTP (remote)

**Bulk upload**
- Admin knowledge intake: PDF / CSV → Supabase Storage → webhook → ingestion pipeline
- Patient uploads: meal/label/menu photos
- Intake checks: type/size limits, schema validation, EXIF/GPS stripped from photos, PII scrubbed before any cloud AI call

**Automated flows**
- n8n: medication & check-in reminders
- n8n: nightly Personal Gut Graph + flare-risk recompute
- n8n: weekly clinician pre-visit report
- Supabase database/storage webhooks → FastAPI ingestion endpoints

**API pull**
- USDA FoodData Central, Open Food Facts, Europe PMC, PubMed E-utilities, Wikidata SPARQL

**AI extraction**
- Vision-language model: meal photo → dishes, ingredients, cooking method, portion, confidence (JSON)
- Labels/menus: vision-language model reads text → normalised ingredients
- Food Composition Table PDF: Docling / pdfplumber → LLM repair of broken rows
- Guideline text → LLM → Rule Cards (condition · component · recommendation · citation) → LLM-judge review
- Wikipedia text → LLM → dish–ingredient graph candidates with provenance → LLM-judge review
- Pydantic schema validation on every output; low confidence → ⚪ "Not sure" / LLM-judge review

## 3. Parsing, formats and cleaning

**Parsers**
- Docling: layout-aware PDF parsing (food composition tables, guideline sections)
- pdfplumber: fallback PDF table extraction
- BeautifulSoup + lxml: Wikipedia HTML, PubMed XML, Europe PMC JATS XML
- Crawl4AI: HTML → LLM-ready Markdown
- pandas: CSV
- DuckDB: Parquet, large CSV
- ruamel.yaml: Rule Cards
- Instructor + Pydantic: LLM/VLM JSON-mode parsing with retry on invalid output
- Pillow + pillow-heif: image decoding (incl. iPhone HEIC)

**Formatters / converters**
- DuckDB: CSV ↔ Parquet
- Docling: PDF → Markdown / JSON
- Crawl4AI / markdownify: HTML → Markdown
- Pillow: photos → resized WebP, EXIF stripped
- YAML Rule Cards → Cypher → Neo4j
- CSV → Neo4j LOAD CSV bulk import
- Jinja2 + WeasyPrint: HTML → PDF pre-visit report (Bangla text shaping via HarfBuzz)
- openapi-typescript: OpenAPI → TypeScript types

**Data cleaning & enrichment**
- Bangla Unicode NFC normalisation, Bangla ↔ ASCII digits, zero-width character cleanup
- Nutrient units normalised per 100 g edible portion (kJ↔kcal, mg/g)
- Local portions → grams (plate, bati, cup, piece)
- Entity resolution: dish names across Wikipedia EN/BN, Wikidata, food table, USDA and user text → one canonical dish ID
- rapidfuzz + BGE-M3 multilingual embeddings + transliteration
- LLM adjudication for ambiguous matches → LLM-judge review
- Ingredient → food-code mapping (Bangladesh food table first, USDA fallback)
- Dedup: barcode (products), DOI/PMID (papers), content hash (chunks)
- AI enrichment: LLM tags dishes with fat level, insoluble fibre, FODMAP groups, lactose, spice level, cooking method
- AI enrichment: Bangla names and aliases
- AI enrichment: contextual chunk headers for RAG
- Check-in range checks; missing days flagged, never silently imputed
- PII scrubbing: Microsoft Presidio + Bangladesh rules (+8801 phone numbers, NID numbers, addresses) + Bengali NER model for Bangla names (CPU), EXIF/GPS removal
- Timestamps stored in UTC, displayed in Asia/Dhaka
- Provenance on every record: source, licence, retrieval time, extraction model + prompt version

**Schema validation**
- Pydantic v2: all ingestion records and LLM outputs
- Zod: frontend forms and API responses
- JSON Schema generated from Pydantic: shared Python ↔ TypeScript contract
- JSON Schema checks on Rule Card YAML in CI (check-jsonschema pre-commit)
- Pandera: DataFrame checks (nutrient ranges, macros ≤ 100 g per 100 g, valid HBI/SCCAI ranges)
- Postgres NOT NULL / CHECK constraints, row-level security, mandatory is_synthetic flag
- Neo4j uniqueness / node-key constraints (dishes, ingredients, components)
- Schemathesis: property-based API contract tests from OpenAPI
- pytest golden-file tests for parsers (food table, PubMed XML, label extraction)

## 4. Storage details
**Schema design**
- Postgres `core`: pseudonymous patient ID, profile (diagnosis, phenotype, stricture flag, disease state), medications, reminders
- Postgres `events`: meal_check, checkin (HBI/SCCAI items, weight, stress, sleep, doses), verdict_feedback, red_flag_event
- Postgres `knowledge`: documents, chunks (text, contextual header, BGE-M3 embedding, tsvector, licence), rule_cards
- Postgres `audit`: consent scopes, access_log, model_run (model + prompt version)
- Postgres `cache`: VLM/LLM results keyed by image SHA-256 / prompt hash (protects free-tier API quotas)
- Neo4j: Dish → CONTAINS → Ingredient → HAS_COMPONENT → Component
- Neo4j: Ingredient → MAPS_TO → FoodCode (Bangladesh food table / USDA)
- Neo4j: RuleCard → ABOUT / APPLIES_TO / CITES → Component / Phenotype / Paper
- Neo4j: Dish → GENTLER_ALTERNATIVE → Dish
- Neo4j: Patient → REACTS_TO {p, n, ci} → Component / Dish (pseudonymous ID only)
- Lakehouse medallion (Delta Lake + DuckDB): bronze (raw snapshots) → silver (cleaned, entity-resolved) → gold (graph imports, evaluation results, synthetic cohort features)
- No identifiable patient rows in the lakehouse

**Partitioning**
- Postgres: monthly range partitions on meal_check and checkin
- Delta bronze: partitioned by source / ingest_date
- Delta gold: evaluations by eval_run; synthetic cohort by sim_run

**Indexes**
- B-tree (patient_id, created_at DESC) on event tables
- GIN on JSONB and tsvector
- pg_trgm trigram for Bangla and English name search, including English-letter spellings of dish names (Postgres has no Bangla stemmer)
- HNSW (cosine, m=16, ef_construction=64) on embeddings
- Partial index on unresolved red-flag events
- Neo4j: unique constraints on IDs; full-text index on EN/BN names and aliases

**Retention**
- Meal photos: 30 days after extraction, unless the user keeps them
- Health records: kept while the account is active; one-click export and delete across Postgres, Neo4j and storage
- Cache entries: 7 days
- LLM traces: 30 days, PII-scrubbed
- Audit / consent logs: 1 year
- Report links: expire in 7 days
- Knowledge snapshots and synthetic data: permanent, versioned, flagged

**Tiered storage**
- Hot: Postgres + Neo4j (live app)
- Warm: Delta silver/gold tables, queried with DuckDB
- Cold: immutable bronze snapshots in Supabase Storage (reproducibility, licence audit)

**Residency & security**
- Supabase region: Mumbai or Singapore (nearest to Bangladesh)
- AES-256 at rest, TLS in transit, app-level encryption for free-text notes

## 5. Visualization

**Visualization details**
- Verdict card: 🟢🟡🔴⚪ icon + label + evidence bar (guideline / composition / personal contribution)
- Symptom trend line (HBI/SCCAI) with meal markers and dose ticks, 7/30/90-day toggle
- Trigger insights: per-component probability with credible interval + exposure count
- Symptom-free-day calendar heatmap
- Flare-risk gauge + top-factor waterfall
- Personal Gut Graph (D3 force layout): edge thickness = trigger probability, tap for evidence, verdict path highlighted
- Interactivity: tap a point → that day's meals and check-in, evidence tooltips, range toggles
- Real-time: Supabase Realtime updates insights after each check-in / graph recompute
- Accessibility: never colour-only (icon + text), colour-blind-safe palette, WCAG AA contrast
- Accessibility: screen-reader summaries, one-line plain-language caption per chart
- Localization: Bangla/English labels, optional Bangla numerals
- Low bandwidth: charts rendered client-side from small JSON, graph view lazy-loaded
- Dark mode

**Dashboards & reports**
- Patient "My Gut" dashboard (in-app, Recharts + D3)
- Clinician pre-visit PDF (Bangla/English): QR share on demand + weekly n8n schedule
- Streamlit + Plotly Model & Evaluation Lab: trigger-recovery curves, verdict confusion matrix, flare-risk calibration, latency, language/bias slices
- Evaluation report (Markdown + charts) exported from the lab after each evaluation run
- Langfuse: LLM traces, tokens, prompt-version comparisons, eval scores
- Neo4j Aura Explore: knowledge-graph QA
## 6. Insights: AI, ML and non-AI

**Methods to tick**
- ✅ Classical ML: LightGBM flare early-warning model + logistic-regression baseline
- ✅ LLM Inference / RAG over data
- ✅ Anomaly Detection: symptom deviation from the patient's own baseline
- ✅ Rule Engine / Heuristics: verdict engine, stricture rules, red flags, clinical index scoring
- ✅ Statistical Analysis: Bayesian N-of-1 trigger discovery, evaluation statistics
- ❌ Deep Learning (we only run pre-trained models; federated PyTorch training is Finals)
- ❌ Forecasting (Prophet etc.)
- ❌ Clustering (trigger-profile clustering for research is Finals)

**AI / ML details**
- Perception: vision-language model (Gemini free tier; Groq-hosted fallback) → dishes, ingredients, cooking method, portion, confidence (JSON)
- Retrieval: BGE-M3 multilingual embeddings (Bangla + English) in pgvector HNSW + keyword/trigram search → reciprocal rank fusion → bge-reranker-v2-m3
- Graph retrieval: Neo4j traversal Dish → Ingredient → Component → Rule Card → Paper
- Explanation: LLM writes Bangla/English explanations only from retrieved evidence, as JSON with citation IDs
- Trigger Discovery (statistical): Bayesian Beta-Binomial per patient × food component
  - Exposure = meal containing the component above a set level; outcome = symptom rise 6–48h later vs personal baseline
  - Guideline-informed population prior → posterior + 90% credible interval
  - "Likely trigger" when P(rate > baseline) > 0.8 with ≥ 3 exposures
  - Confounders (stress, missed doses) handled by stratification
- Flare Early Warning (classical ML): LightGBM, target = flare onset within 7 days
  - Features: 7/14-day HBI/SCCAI mean and slope, stool frequency, blood flag, missed doses, stress, sleep, weight change, trigger-exposure load
  - Patient-grouped time split (no leakage) · isotonic calibration · SHAP top factors per alert
  - Baselines: logistic regression and the v0 rule score
- Anomaly detection: EWMA / rolling z-score on each patient's symptom indices and stool frequency (≥ 2 SD for 2 days → early-warning feature)
- Training data: simulated IBD cohort (500 patients × 180 days, injected triggers, labelled SYNTHETIC)
- Test data: team-labelled 200-food verdict set · team-captured ~300 Bangladeshi meal photos · guideline Q&A set · red-flag suite
- Metrics: dish recognition top-1 / top-3 accuracy
- Metrics: verdict accuracy + macro-F1, with 🔴 recall prioritised
- Metrics: retrieval Recall@5 and MRR; Ragas faithfulness and answer relevance
- Metrics: trigger recovery precision / recall / F1 and days-to-detection
- Metrics: flare model AUROC, AUPRC, Brier score, calibration curve, alert lead time
- Metrics: red-flag recall (target 100%); p90 scan-to-verdict latency (< 5 s)
- Bias slices: Bangla vs English input, sex, disease phenotype
- Honesty: flare-model and trigger results are reported as results on simulated data

**Non-AI analytics**
- Verdict engine: deterministic weighted score (guideline severity × component level × disease-state multiplier + personal posterior) → 🟢🟡🔴 thresholds; low confidence → ⚪; unit-tested
- Hard overrides before any LLM output: stricturing Crohn's (insoluble fibre, skins, seeds, nuts → 🔴); red-flag symptoms → escalation
- Clinical indices: Harvey-Bradshaw Index and SCCAI computed from check-in items with standard published activity thresholds
- Early warning v0: rule score (index rise, blood, missed doses, weight loss past a threshold)
- Red-flag rule set: structured answers + Bangla/English keyword patterns (romanised-Bangla phrases kept as a safety net), run before the LLM
- SQL aggregations: medication adherence %, symptom-free days and streaks, weekly averages, exposures per component
- Evaluation statistics: bootstrap 95% confidence intervals on every metric
- Evaluation statistics: McNemar's test, verdict engine vs an LLM-only baseline
- Product KPIs: 4-week logging retention, scans per day, latency, cache hit rate, free-tier quota usage

**How insights are delivered**
- Verdict card, instantly after a scan: verdict + why + citations + a gentler alternative
- "My Gut" dashboard: trends, trigger insights, Personal Gut Graph
- Web push notifications (PWA): medication and check-in reminders
- Web push notifications (PWA): rising flare risk with its top factors
- Web push notifications (PWA): new trigger found ("fried food: 4 of 5 times")
- Weekly AI summary in Bangla/English, written only from computed statistics
- Red-flag escalation screen: stops diet advice and shows who to contact now
- Clinician pre-visit PDF, shared by QR code / link
- Streamlit Evaluation Lab for the team and judges

**Finals additions (not in the form yet):** federated learning (Flower + PyTorch + Opacus differential privacy) · mixed-effects confounder model · wearable features (resting HR, HRV, sleep) · trigger-profile clustering for research
## 7. Pipelines and orchestration

**Orchestration**
- n8n (self-hosted, Docker): reminders, nightly recompute, weekly clinician report, ingestion after admin upload
- Python pipeline CLI (Typer + Makefile): knowledge build crawl → parse → resolve → enrich → load (bronze → silver → gold → Neo4j / pgvector)
- Pipeline steps are idempotent and can re-run from any stage
- LangGraph: meal-check agent pipeline (details in the AI section)

**Scheduling / triggers**
- n8n cron: per-user medication and check-in reminder times (Asia/Dhaka)
- n8n cron: 02:00 nightly Personal Gut Graph + flare-risk recompute
- n8n cron: weekly pre-visit report
- Supabase database webhooks: new meal_check / checkin → FastAPI → red-flag check + incremental trigger update
- Supabase Storage trigger: admin upload → ingestion pipeline
- pg_cron: expire cache entries, delete meal photos past retention
- Manual: `make knowledge` for full knowledge rebuilds

**Streaming / real-time**
- Supabase Realtime (Postgres changes over WebSocket): dashboard updates after check-ins and recomputes
- Server-Sent Events from FastAPI stream each scan in stages: dishes found → verdict → explanation text
- Event-driven webhooks instead of Kafka (event volume is low; no broker needed)

## 8. Outbound: APIs and distribution

**Outbound APIs**
- FastAPI REST, versioned `/v1`
- Endpoints: `POST /v1/meal-checks` (photo/text → verdict), `GET /v1/meal-checks/{id}`, `POST /v1/checkins`
- Endpoints: `GET /v1/insights/triggers`, `GET /v1/insights/flare-risk`, `POST /v1/reports/previsit`, `GET /v1/foods/search`
- Auth: Supabase Auth JWT (email OTP / Google), verified in FastAPI + Postgres row-level security
- Rate limits: per-user token bucket (slowapi) + per-provider quota guard for free-tier AI APIs
- OpenAPI 3.1 docs (Swagger UI / ReDoc) + generated TypeScript client
- CORS locked to the app domain; request size limits

**Webhooks and exports**
- Patient data export: JSON + CSV, one click (access / portability)
- Clinician pre-visit PDF: signed link expiring in 7 days + QR code
- Web Push (VAPID) notifications sent by n8n
- Evaluation exports: Parquet / CSV results + Markdown report in the repo

**Embeddings / model serving**
- Ollama on the team GPU (AMD RX 7700 XT, 12 GB, ROCm; quantized Q4_K_M): finite GPU jobs on Ubuntu (contextual headers, aliases, test sets, evaluation judge)
- BGE-M3 + bge-reranker-v2-m3 (sentence-transformers) inside the always-on backend on CPU; on the GPU for batch corpus embedding
- MCP server we expose: `happygut-foodgraph` over Streamable HTTP (search_dish, get_components, explain_verdict_path)
- Free-tier cloud LLM/VLM APIs for primary reasoning and vision (models listed in the AI section)

## 9. Open-source stack
- PostgreSQL + pgvector + pg_trgm + pg_cron: relational store, vector search, Bangla fuzzy search, scheduled cleanup
- Supabase: Auth, Storage, Realtime, database webhooks
- Neo4j: Food Knowledge Graph + Personal Gut Graph
- DuckDB: in-process analytics over the lakehouse
- Delta Lake (delta-rs): versioned bronze/silver/gold tables with time travel
- Scrapy: Wikipedia cuisine crawling
- Crawl4AI: guideline pages → Markdown
- Docling / pdfplumber: PDF and table parsing
- BeautifulSoup + lxml: HTML / XML parsing
- pandas: tabular cleaning
- Pydantic + Instructor: schemas and validated LLM output
- Pandera: DataFrame quality checks
- Microsoft Presidio: PII detection and anonymisation
- rapidfuzz: fuzzy dish-name matching
- BGE-M3 + bge-reranker-v2-m3 (sentence-transformers): multilingual embeddings and reranking
- Ollama + open-weight models (Qwen, Gemma, Llama, DeepSeek-R1-Distill): finite local GPU jobs
- LangGraph: agent orchestration
- scikit-learn + LightGBM + SHAP: flare model, baselines, explanations
- NumPy / SciPy: Bayesian trigger statistics, bootstrap confidence intervals
- FastAPI: backend API and SSE streaming
- React + Vite (vite-plugin-pwa) + Tailwind + shadcn/ui + Zod: PWA frontend and validation
- Recharts + D3.js: patient charts and the Gut Graph
- Streamlit + Plotly: Evaluation Lab
- Jinja2 + WeasyPrint: PDF reports
- Langfuse: LLM tracing and evaluation scores
- Ragas: RAG evaluation
- pytest + Schemathesis: tests and API contract tests
- Pillow: image processing and EXIF stripping
- n8n: workflow automation (source-available under its Sustainable Use License, not OSI open source)

## 10. Quality, governance and observability

**Data quality**
- Pandera checks at every silver/gold step (ranges, nulls, uniqueness)
- Completeness: every dish has ingredients and component tags; every Rule Card has a citation and licence
- Unmatched-ingredient rate reported on each knowledge build
- Neo4j orphan-node checks (e.g. dishes without components)
- Freshness: knowledge snapshot date shown in the admin view; USDA / Open Food Facts refreshed monthly
- Human review queue for every LLM-extracted fact, plus a 10% random re-audit
- Golden-file tests on parsers
- CI regression gate: verdict accuracy and red-flag recall on the evaluation sets must not drop
- `is_synthetic` flag enforced on all simulated data

**Privacy and compliance**
- Pseudonymous patient IDs; identity kept only in Supabase Auth
- Presidio + Bangladesh rules + Bengali NER strip PII before any cloud AI call; EXIF / GPS removed from photos
- Consent scopes (care, clinician sharing, research aggregates): opt-in, revocable, logged
- Row-level security per patient; service role only in the backend (least privilege)
- AES-256 at rest, TLS in transit, signed expiring URLs
- One-click export + cascading delete (right of access / erasure)
- Data minimisation: photos deleted after 30 days; no location collected
- Research outputs are aggregates only, with small-group suppression (k ≥ 10)
- Aligned with GDPR principles and HIPAA-style safeguards; Bangladesh data-protection law tracked (*verify current status*)
- Positioned as self-management support, not a medical device; disclaimer shown in the app
- The prototype holds no real patient data; all test data is synthetic and labelled

**Lineage and observability**
- Provenance on every record: source, licence, retrieved_at, model + prompt version
- Medallion lineage: every silver/gold row keeps its bronze source ID
- Each evaluation run records its Delta table version + git commit (reproducible results)
- Every verdict stores its evidence IDs → traceable to the Rule Card → the paper
- Langfuse traces every LLM/VLM call (latency, tokens, prompt version)
- Structured JSON logs (structlog)
- n8n failure alerts; red-flag events recorded in the audit log

**Cost and performance**
- Running cost: $0 (free tiers + the team's GPU)
- Postgres cache by image SHA-256 / prompt hash: repeat dishes need no API call
- Model routing: small/fast model for classification, larger model only for explanations
- Local Ollama handles PII scrubbing, Bangla normalisation, and fallback when a free-tier quota runs out
- Per-provider quota guard with automatic fallback (Gemini → Groq)
- Compact prompts: structured evidence (IDs + short facts) and the top 5 reranked chunks, not raw documents
- Photos downscaled to ≤ 1024 px WebP before the vision model (fewer tokens)
- Precomputed dish component profiles, so the verdict decision itself needs no LLM call
- Embeddings and enrichment run as offline GPU batch jobs
- Batch LLM work and corpus embeddings run as finite local GPU jobs (Q4_K_M models, ROCm PyTorch), never as a paid API
- SSE streaming for faster perceived response; target p90 < 5 s scan-to-verdict
- Partitioning and indexes as in §4
## 11. Other data stack notes

**AI-native patterns**
- Personal Gut Graph: one population food knowledge graph + a per-patient layer of learned REACTS_TO edges
- "LLM perceives, engine decides": AI for reading and explaining; a deterministic, unit-tested engine for the verdict
- Evidence-carrying verdicts: every verdict stores its evidence IDs, so any answer can be audited back to the paper
- Licence-aware ingestion: each source's licence decides whether full text or only a cited Rule Card is stored
- Human-in-the-loop curation: LLM extracts facts, humans approve before they enter the graph
- Privacy before the cloud: PII removed inside our backend (Presidio + Bangladesh rules + Bengali NER); cloud models only see de-identified text
- Synthetic cohort as test oracle: injected ground-truth triggers make trigger discovery measurable

**Agent-driven data ops**
- Knowledge-gap loop: every ⚪ "Not sure" or unmatched dish is queued; an enrichment agent drafts graph facts → LLM-judge review → graph update
- Data flywheel: "was this right for you?" feedback feeds Trigger Discovery and grows the evaluation sets
- Curation via MCP: a coding agent uses the Neo4j and Supabase MCP servers to find orphan nodes and unmatched ingredients and propose fixes as reviewable diffs

**Future roadmap**
- Federated learning (Flower + differential privacy) for population trigger priors
- Wearables (Health Connect / Fitbit) and lab-report ingestion
- Bangla voice logging
- Offline-first PWA with an on-device small model
- HL7 FHIR integration with hospitals
- Differentially private research lakehouse + Metabase portal + happygut-research MCP
- New cuisines and languages as plug-in graph modules (India, Pakistan, Middle East)
- Open release of the Bangladeshi Food Knowledge Graph (respecting source licences)

## 12. Publishing local environment to the internet

**Tools**
- ✅ ngrok: development only (on Windows)
- ❌ Tailscale Funnel: dropped. The live app runs entirely on cloud services, so no local machine is published

**Tunneling usage notes**
- ngrok exposes the local FastAPI dev server so Supabase database/storage webhooks and n8n callbacks can reach it during development
- Free static domain, so the webhook URL stays the same between sessions
- Every webhook carries a shared-secret header that the dev server checks
- Started per dev session and closed afterwards; never used in production (production runs on Hugging Face Spaces)
