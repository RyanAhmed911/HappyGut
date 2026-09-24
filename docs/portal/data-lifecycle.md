# Portal text: Data lifecycle (prototype, Oct 31)

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
2. Generated Bangla/Banglish evaluation sets
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
- Guideline text → LLM → Rule Cards (condition · component · recommendation · citation) → human review
- Wikipedia text → LLM → dish–ingredient graph candidates with provenance → human review
- Pydantic schema validation on every output; low confidence → ⚪ "Not sure" / human review

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
- Banglish → Bangla transliteration (Dakshina) before matching
- Nutrient units normalised per 100 g edible portion (kJ↔kcal, mg/g)
- Local portions → grams (plate, bati, cup, piece)
- Entity resolution: dish names across Wikipedia EN/BN, Wikidata, food table, USDA and user text → one canonical dish ID
- rapidfuzz + BGE-M3 multilingual embeddings + transliteration
- LLM adjudication for ambiguous matches → human review
- Ingredient → food-code mapping (Bangladesh food table first, USDA fallback)
- Dedup: barcode (products), DOI/PMID (papers), content hash (chunks)
- AI enrichment: LLM tags dishes with fat level, insoluble fibre, FODMAP groups, lactose, spice level, cooking method
- AI enrichment: Bangla names and aliases
- AI enrichment: contextual chunk headers for RAG
- Check-in range checks; missing days flagged, never silently imputed
- PII scrubbing: Microsoft Presidio + local LLM (Bangla names, +8801 phone numbers, addresses), EXIF/GPS removal
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
- pg_trgm trigram for Bangla/Banglish name search (Postgres has no Bangla stemmer)
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
