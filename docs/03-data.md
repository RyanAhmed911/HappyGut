# Step 3: Data lifecycle and engineering

> Status: **§0 prototype selections + §1–12 drafted** (2026-09-24). Later sections are filled in as we work through the portal's data-lifecycle form.
> Rule (CLAUDE.md #8): every source is listed here with its licence **before** any code ingests it. Rows marked *verify* must be checked and updated before first ingestion.

**Tier legend:** **MVP** = needed for the hero flow by Oct 31 · **Finals** = Nov–Dec hardening · **Roadmap** = pitch only

---

## 0. Prototype portal selections (authoritative for the Oct 31 form)

> **Rule:** tick an item only if it earns points (under the cap or a bonus) **and** will really exist by Oct 31. §1–5 below are the full design; anything tagged *Finals* there is **not** entered in the preliminary form.

| Form section | Tick for Oct 31 | Finals only (not in the form yet) |
|---|---|---|
| Data sources | Internal · External APIs · Public Web · Open Datasets · User Uploads · Synthetic | IoT / Sensor |
| Acquisition | Web Scrapers · AI Extraction · MCP · Bulk Upload · Automated Flows · API Pull | RSS · OCR (the vision model does it) · Speech-to-Text |
| Formats | JSON · CSV · PDF · Images | — (others are true but earn nothing past the cap of 4) |
| Storage | Relational (Postgres) · Vector (pgvector) · Object (Supabase Storage) · Graph (Neo4j) · Lakehouse (Delta/Parquet) · Warehouse (DuckDB) | NoSQL (IndexedDB) · Cache (Redis) |
| Visualization | Recharts · D3.js · Plotly · Streamlit | Grafana · Metabase |

**Moved to Finals:**
- Wearables (Fitbit / Google Health API, export import, sync flow)
- Voice notes (faster-whisper, ffmpeg, Common Voice)
- Lab reports (OCR, LOINC)
- DGDA registry + Playwright scraper
- IBDMDB calibration
- RSS watcher
- `happygut-journal` and `happygut-research` MCP servers
- Tesseract fallback
- FHIR export

**Prototype infrastructure:** one Supabase project (Postgres + pgvector + Storage) · Neo4j AuraDB Free · Hugging Face Spaces (backend + n8n) · Windows for development and loading data (DuckDB, Delta files) · finite Ubuntu GPU jobs for enrichment, embeddings, evaluation and fine-tuning.

---

## 1. Data sources

### 1.1 Portal checkbox selection

| Portal category | Select? | Why |
|---|---|---|
| Internal (own DB / app data) | ✅ | Profiles, meal checks, verdicts, check-ins, adherence, verdict feedback, curated knowledge |
| External APIs (paid/free) | ✅ | USDA FoodData Central, Open Food Facts, Europe PMC, wearable API. All free |
| Public Web (scraping) | ✅ | Wikipedia cuisine pages, open-access guideline pages, Bangladeshi drug registry |
| Open Datasets (Kaggle, HF, gov) | ✅ | Bangladesh Food Composition Table, USDA bulk, Wikidata, Dakshina, Common Voice, IBDMDB |
| User Uploads / Bulk Import | ✅ | Meal/label/menu photos, voice notes, lab reports, wearable exports, admin knowledge uploads |
| IoT / Sensor / Streaming | ❌ *(Finals)* | Wearable heart rate, HRV, sleep and steps |
| Third-party / Partner Data | ❌ | We have no partner data agreements. We're already at 5/5 points for source types, so ticking it gains nothing and a judge could question it |
| Synthetic / AI-generated Data | ✅ | Simulated patient cohort with injected triggers, generated Bangla/Banglish evaluation sets |

### 1.2 Source catalogue

#### A. Internal: HappyGut's own data
| ID | Source | What it holds / why we need it | Tier |
|---|---|---|---|
| IN-1 | **App database** (Supabase Postgres) | Patient profile (diagnosis, phenotype, current state, medications, known triggers), meal checks and verdicts, daily check-ins (HBI/SCCAI items, weight, stress, sleep, doses taken), reminders | MVP |
| IN-2 | **Verdict feedback** | "Was this right for you?" responses on each verdict. They label real-world outcomes and feed Trigger Discovery and evaluation | MVP |
| IN-3 | **Personal Gut Graph** (Neo4j) | Per-patient learned tolerances: `REACTS_TO {p, n, ci}` edges derived from IN-1 | MVP |
| IN-4 | **HappyGut Rule Cards** | Team-authored, structured rules extracted from guidelines (condition → food component → recommendation → citation). This is how we use guidance whose licence doesn't allow storing full text | MVP |
| IN-5 | **Operational telemetry** | LLM traces, latency, token usage, evaluation-run results | MVP |

#### B. External APIs (all free)
| ID | Source | Use | Access | Licence | Tier |
|---|---|---|---|---|---|
| API-1 | **USDA FoodData Central API** | Nutrient composition (fat, fibre, lactose, sugars) for ingredients missing from the Bangladesh table | REST + free API key | Public domain (CC0) | MVP |
| API-2 | **Open Food Facts API** | Packaged-food lookup by barcode: ingredient lists, additives, allergens, including products sold in Bangladesh | REST, no key | Database: ODbL · images: CC BY-SA | MVP |
| API-3 | **Europe PMC REST API** | Find and fetch open-access IBD nutrition papers and guidelines; returns each article's licence, so licence filtering is automatic | REST, no key | Per article (we only store full text for CC-licensed articles) | MVP |
| API-4 | **NCBI PubMed E-utilities** | Citation metadata (PMID, DOI, authors) so every verdict's citation resolves to a real paper | REST + free API key | Metadata free to use; abstracts are publisher copyright (not stored) | MVP |
| API-5 | **Fitbit Web API / Google Health platform** | Resting HR, HRV, sleep, steps for Flare Early Warning, with patient OAuth consent | OAuth REST | Per-user consent; platform terms (*verify the current API, as Google is migrating Fitbit APIs*) | Finals |

#### C. Public web (scraping and crawling)
| ID | Source | Use | Licence | Tier |
|---|---|---|---|---|
| WEB-1 | **Wikipedia**: Bangladeshi and Bengali cuisine articles and dish pages (English and Bangla editions) | Dish list, descriptions, typical ingredients and preparation for the Food Knowledge Graph | CC BY-SA 4.0 (attribution kept in graph metadata) | MVP |
| WEB-2 | **Open-access guideline and society pages** (ESPEN, IOIBD, AGA publications) | Source text for Rule Cards and the guideline RAG corpus | Per document (*verify each*: CC-licensed → full-text RAG; free-to-read only → we store Rule Cards with citations, not the text) | MVP |
| WEB-3 | **DGDA Bangladesh drug database** (Directorate General of Drug Administration) | Map Bangladeshi medication brand names to generics so patients can log the medicines they actually buy | Government public information (*verify terms*) | Finals |

#### D. Open datasets
| ID | Dataset | Use | Licence | Tier |
|---|---|---|---|---|
| OD-1 | **Food Composition Table for Bangladesh (2013)**, INFS, University of Dhaka (distributed via FAO/INFOODS) | Core nutrient data for Bangladeshi foods, parsed from PDF tables | Freely published (*verify reuse terms; cite*) | MVP |
| OD-2 | **USDA FoodData Central bulk download** | Offline copy of API-1 for batch knowledge-graph builds | CC0 | MVP |
| OD-3 | **Wikidata** | Dish ↔ ingredient relations, **Bangla labels** and aliases, cuisine of origin | CC0 | MVP |
| OD-4 | **Published FODMAP composition tables** (peer-reviewed papers, e.g. Varney et al. 2017) | Fructan/GOS/polyol/lactose/excess-fructose levels per food. *Monash University's app database is proprietary and is not used* | Facts extracted with citation (*verify per paper*) | MVP |
| OD-5 | **Google Dakshina dataset** (Bengali romanisation subset) | Banglish ↔ Bangla transliteration pairs, so "kacchi", "bhorta" and "dal" resolve to dishes | CC BY-SA 4.0 | MVP |
| OD-6 | **Mozilla Common Voice: Bengali** | Evaluate voice-logging speech recognition accuracy (evaluation only) | CC0 | Finals |
| OD-7 | **IBDMDB / HMP2 public metadata** (Inflammatory Bowel Disease Multi'omics Database) | Real longitudinal IBD disease-activity and diet-questionnaire data, used to **calibrate and sanity-check** the synthetic cohort and early-warning score | Public research data (*verify terms of use*) | Finals |
| OD-8 | **Open food-image datasets** with Bangladeshi/South Asian dishes (Kaggle / Hugging Face) | Evaluate dish recognition. We use a vision-language model and don't train a vision model from scratch | *Select only datasets with a clear licence* | MVP (eval) |
| OD-9 | **LOINC** | Standard codes for lab tests (CRP, faecal calprotectin, haemoglobin, albumin) from uploaded reports | Free with licence acceptance and attribution | Finals |

#### E. User uploads and bulk import
| ID | Input | Use | Tier |
|---|---|---|---|
| UP-1 | **Meal, plate, menu and label photos** | Main input to the hero flow (vision → dishes/ingredients) | MVP |
| UP-2 | **Voice notes** (Bangla / English / Banglish) | Hands-free meal logging and check-ins | MVP |
| UP-3 | **Lab report photos/PDFs** | Extract CRP, calprotectin, Hb and albumin trends for the early warning and pre-visit report | Finals |
| UP-4 | **Wearable export files** (Google Takeout Fitbit / Samsung Health CSV/JSON) | Wearable signals without a live API integration | MVP (demo) |
| UP-5 | **Admin knowledge upload** | Team uploads guideline PDFs and curated dish lists, which trigger the ingestion pipeline | MVP |
| UP-6 | **Team-captured meal photo set** | ~300 photos of real Bangladeshi meals taken by the team. Fully licensed, the main dish-recognition test set | MVP |

#### F. IoT / sensor / streaming
| ID | Stream | Use | Tier |
|---|---|---|---|
| IOT-1 | **Wearables**: resting heart rate, HRV, sleep, steps | Physiological signals for Flare Early Warning. File import (UP-4) for the MVP; live sync via API-5 and Android Health Connect for Finals | MVP (import) / Finals (live) |
| IOT-2 | **App event stream**: meal logged, check-in submitted, red flag detected | Real-time triggers for recomputing the Personal Gut Graph and sending alerts | MVP |

#### G. Synthetic / AI-generated (always labelled SYNTHETIC)
| ID | Dataset | How it's made | Use | Tier |
|---|---|---|---|---|
| SYN-1 | **Synthetic IBD patient cohort** (e.g. 500 patients × 180 days) | Python simulator: diets drawn from real Bangladeshi dishes (OD-1/OD-3), symptom model with **known injected triggers**, noise and confounders (stress, sleep, missed doses, menstrual cycle), parameters taken from literature | Validates Trigger Discovery (precision/recall, days-to-detection); trains early-warning v1; runs the federated-learning simulation | MVP |
| SYN-2 | **Demo persona history** | 60-day history for the video persona, generated by SYN-1 | Believable, honest demo | MVP |
| SYN-3 | **Bangla/Banglish evaluation utterances** | Generated with an LLM (local Llama 3.2 in a GPU session, or a free cloud tier), then reviewed by the team | Tests voice/text understanding and dish-name resolution | MVP |
| SYN-4 | **Red-flag test suite** | Paraphrases of emergency symptoms in Bangla, English and Banglish, generated and then reviewed | Safety tests (target: 100% recall) | MVP |
| SYN-5 | **Guideline Q&A evaluation set** | Question–answer–source triples generated from Rule Cards, then reviewed | RAG retrieval and faithfulness evaluation | MVP |

### 1.3 Deliberately **not** used
| Source | Why not |
|---|---|
| Monash FODMAP app database | Proprietary; scraping would breach the terms |
| Patient forums and social media (Reddit, Facebook groups) | Personal health data without consent, even if public |
| Real patient records | We have no ethics approval or partnership. All patient data in this project is synthetic or the team's own |

---

### 1.4 Portal text: "Data source details"
> Plain text, ready to paste.

HappyGut's prototype combines six types of data source, each with a documented licence. Internal: our Supabase app database (patient profiles, meal checks, verdicts, daily check-ins using Harvey-Bradshaw Index and SCCAI items, medication adherence and "was this right for you?" verdict feedback), the Neo4j Personal Gut Graph of learned tolerances, and team-authored Rule Cards that turn published IBD guidance into structured, cited rules. External free APIs: USDA FoodData Central (CC0 nutrient data), Open Food Facts (ODbL barcode lookup of packaged foods sold in Bangladesh), Europe PMC (open-access IBD nutrition literature, filtered automatically by licence) and PubMed E-utilities (citation metadata so every claim links to a real paper). Public web: Wikipedia Bangladeshi cuisine pages in English and Bangla (CC BY-SA) for dish descriptions and ingredients, and open-access ESPEN, IOIBD and AGA guideline documents. Open datasets: the Food Composition Table for Bangladesh (INFS, University of Dhaka), Wikidata (CC0) for dish-ingredient relations and Bangla labels, published FODMAP composition tables, and Google's Dakshina dataset for Banglish-to-Bangla transliteration. User uploads: meal, menu and label photos, plus a team-captured set of about 300 real Bangladeshi meal photos used as our test set. Synthetic data: a clearly labelled simulated cohort of IBD patients with known injected food triggers, used to measure how accurately our Trigger Discovery engine recovers them, plus generated and human-reviewed Bangla/Banglish, red-flag and guideline Q&A evaluation sets. We deliberately exclude proprietary databases (such as Monash FODMAP), social-media health posts and any real patient records. Wearables, voice notes, lab reports and a Bangladeshi medicine registry are planned for the finals phase.

---

## 2. Acquisition methods

### 2.1 Portal checkbox selection
| Method | Select? | Used for |
|---|---|---|
| Web Scrapers | ✅ | Wikipedia cuisine pages, open-access guidelines, DGDA registry |
| AI Extraction | ✅ | Meal photos, labels, guideline text → Rule Cards, dish descriptions → graph facts |
| MCP Servers for data access | ✅ | Our own food-graph / journal / research servers + Supabase, Neo4j, Filesystem |
| Bulk Upload | ✅ | Admin knowledge intake, patient photos, lab reports, wearable exports |
| Automated Flows | ✅ | n8n, Supabase webhooks, scheduled GitHub Actions |
| API Pull / SDK | ✅ | USDA, Open Food Facts, Europe PMC, PubMed, Wikidata SPARQL, Fitbit |
| RSS / Atom Feeds | ❌ *(Finals)* | PubMed saved-search and journal feeds for new IBD diet research (Finals) |
| Email Inbox | ❌ | Not needed |
| OCR | ❌ | The vision-language model reads labels and menus; Tesseract and lab-report OCR are Finals |
| Speech-to-Text | ❌ *(Finals)* | Bangla/English/Banglish voice logging |

### 2.2 Scrapers / crawlers
- **Scrapy spiders**: Wikipedia Bangladeshi and Bengali cuisine categories, English and Bangla
- **Crawl4AI** (open source): open-access guideline pages → clean markdown for RAG
- **Playwright headless**: DGDA drug registry (JavaScript-rendered, paginated)
- **Wikidata SPARQL harvester**: dishes, ingredients, Bangla labels
- **Crawl etiquette**: robots.txt respected · 1 req/s throttle · identifying User-Agent · ETag caching · exponential-backoff retries
- **No anti-bot evasion** (no CAPTCHA or paywall bypass)
- **Licence gate**: each job is tagged with its source licence; content that isn't openly licensed goes to Rule Cards only

### 2.3 MCP servers for data access
**Built by us**
- `happygut-foodgraph`: food knowledge graph queries (`search_dish`, `get_components`, `explain_verdict_path`)
- `happygut-journal`: consent-scoped patient log and pre-visit report access for clinicians' MCP clients (Finals)
- `happygut-research`: differentially private aggregate trigger statistics (Finals)

**Used**
- Supabase MCP: Postgres schema and queries
- Neo4j Cypher MCP: graph queries and curation
- Filesystem MCP: raw data-lake folders
- Playwright MCP: building and debugging scrapers

**Transports**: stdio (local) · Streamable HTTP (remote)

### 2.4 Bulk upload, automated flows, AI extraction

**Bulk upload**
- Admin knowledge intake: PDF / CSV / XLSX → Supabase Storage `raw/` → webhook → ingestion pipeline
- Patient uploads: meal/label/menu photos, voice notes, lab report PDFs/photos, wearable exports (CSV / JSON / Takeout ZIP)
- Intake checks: type and size limits, schema validation, **EXIF/GPS stripped from photos**, PII scrub before any cloud call

**Automated flows**
- n8n: medication and check-in reminders
- n8n: nightly Personal Gut Graph + flare-risk recompute
- n8n: weekly clinician pre-visit report
- n8n: wearable sync (Finals)
- n8n: RSS watch for new IBD diet papers → LLM triage → human review queue (Finals)
- Supabase database / storage webhooks → FastAPI ingestion endpoints
- Scheduled GitHub Actions: weekly scraper runs, USDA / Open Food Facts delta refresh

**API pull**
- USDA FoodData Central · Open Food Facts · Europe PMC · PubMed E-utilities · Wikidata SPARQL · Fitbit / Google Health (Finals)

**AI extraction**
- Vision-language model: meal photo → dishes, ingredients, cooking method, portion, confidence (JSON)
- Labels and menus: VLM OCR first, Tesseract (Bangla + English) as fallback → normalised ingredient list
- Food-table PDF: Docling / pdfplumber tables → LLM repair of broken rows
- Guideline text → LLM → Rule Cards (condition · component · recommendation · citation) → human review
- Wikipedia text → LLM → dish–ingredient graph candidates with provenance → human review
- Lab reports: OCR + LLM → LOINC-coded values (Finals)
- Voice: faster-whisper (local GPU) → Banglish transliteration (Dakshina) → intent and entity extraction
- Every output is validated against a Pydantic schema; low confidence → ⚪ "Not sure" or human review

## 3. Parsing, formats and cleaning

### 3.1 Formats handled
| Format | Select? | Where it appears |
|---|---|---|
| JSON | ✅ | API responses (USDA, Open Food Facts, Fitbit), LLM structured outputs, wearable exports |
| CSV | ✅ | USDA bulk, wearable exports, graph import files, research exports |
| XLSX | ➖ used, not ticked | Admin uploads (curated dish lists, portion tables) |
| PDF | ✅ | Guidelines, Bangladesh food table, lab reports; pre-visit report output |
| Parquet | ➖ used, not ticked | Lakehouse tables, synthetic cohort, evaluation results |
| Avro | ❌ | Not used |
| XML | ➖ used, not ticked | PubMed E-utilities, Europe PMC full text (JATS) |
| YAML | ➖ used, not ticked | Rule Cards (version-controlled), pipeline configuration |
| JSONL | ➖ used, not ticked | Open Food Facts dump, evaluation sets, LLM batch jobs |
| Markdown | ➖ used, not ticked | Crawled pages converted for RAG, prompt library |
| HTML | ➖ used, not ticked | Scraped pages (Wikipedia, guideline sites, DGDA) |
| Images | ✅ | Meal/label/menu photos, lab report photos |
| Audio | ➖ used, not ticked | Voice notes |
| Video | ❌ | Not used |
| Protobuf | ❌ | Not used |

### 3.2 Parsers
- Docling: layout-aware PDF parsing (food-table tables, guideline sections)
- pdfplumber / PyMuPDF: fallback table and text extraction
- BeautifulSoup + lxml: Wikipedia HTML, PubMed XML, Europe PMC JATS XML
- Crawl4AI: HTML → LLM-ready Markdown
- pandas / Polars (+ openpyxl): CSV, XLSX
- DuckDB: JSONL, Parquet, CSV at scale
- orjson: fast JSON
- ruamel.yaml: Rule Cards
- Instructor + Pydantic: LLM/VLM JSON-mode parsing with automatic retry on invalid output
- Tesseract (Bangla + English) + VLM OCR: labels, menus, lab reports
- faster-whisper: audio → text
- Pillow (+ pillow-heif): image decode, including iPhone HEIC

### 3.3 Formatters and converters
- DuckDB: CSV / JSONL ↔ Parquet (lakehouse)
- Docling: PDF → Markdown / JSON
- Crawl4AI / markdownify: HTML → Markdown
- ffmpeg: WebM / OGG / M4A → 16 kHz mono WAV for speech-to-text
- Pillow: photos → resized WebP, EXIF stripped (low bandwidth + privacy)
- ruamel.yaml → Cypher: Rule Cards → Neo4j
- CSV → Neo4j `LOAD CSV`: bulk graph import
- Jinja2 + WeasyPrint: HTML → PDF pre-visit report (Bangla shaping via HarfBuzz)
- fhir.resources: HL7 FHIR JSON export for clinicians (Finals)
- openapi-typescript: OpenAPI → TypeScript types for the frontend

### 3.4 Data cleaning and enrichment
- Bangla text: Unicode NFC normalisation, Bangla ↔ ASCII digits (০–৯), zero-width character cleanup
- Banglish → Bangla transliteration (Dakshina-based) before matching
- Units: nutrients per 100 g edible portion; kJ ↔ kcal; mg / g harmonised
- Local portions → grams (plate, bati, cup, piece)
- Entity resolution: dish names across Wikipedia EN/BN, Wikidata, food table, USDA and user text → one canonical dish ID
  - rapidfuzz fuzzy matching + BGE-M3 multilingual embeddings + transliteration
  - LLM adjudication for ambiguous matches → human review
- Ingredient → food-code mapping: Bangladesh food table first, USDA as fallback
- Dedup: products by barcode, papers by DOI/PMID, chunks by content hash, near-duplicate pages by MinHash
- AI enrichment: LLM tags each dish (fat level, insoluble fibre, FODMAP groups, lactose, spice level, cooking method) with provenance
- AI enrichment: Bangla names and aliases
- AI enrichment: contextual chunk headers for RAG
- Wearables: physiologically impossible values removed, rolling-median artefact filter
- Check-ins: range checks; missing days flagged, never silently imputed
- PII scrub: Microsoft Presidio + Bangladesh rules (+8801 phone numbers, NID numbers, addresses) + Bengali NER model for Bangla names (CPU); EXIF / GPS removed from photos
- Time: stored in UTC, displayed in Asia/Dhaka
- Provenance on every record: source, licence, retrieved_at, extraction model + prompt version

### 3.5 Schema validation
- Pydantic v2: every ingestion record and LLM output
- Zod: frontend forms and API responses
- JSON Schema generated from Pydantic: a shared contract between Python and TypeScript
- JSON Schema check in CI on Rule Card YAML (check-jsonschema pre-commit hook)
- Pandera: DataFrame checks (nutrient ranges; per-100 g macros ≤ 100 g; valid HBI/SCCAI item ranges)
- Postgres: NOT NULL / CHECK constraints, row-level security, and a mandatory `is_synthetic` flag
- Neo4j: uniqueness and node-key constraints on dishes, ingredients and components
- Schemathesis: property-based contract tests generated from the OpenAPI spec
- pytest: golden-file tests for the parsers (food table, PubMed XML, label OCR)

## 4. Storage

### 4.1 Storage targets (all free tier)
| Target | Select? | Technology | Holds |
|---|---|---|---|
| Relational | ✅ | Supabase Postgres | Profiles, meal checks, verdicts, check-ins, meds, reminders, consent, audit |
| NoSQL | ❌ *(Finals)* | IndexedDB on the device (Dexie.js) | Offline-first queue of meal logs and check-ins, cached recent verdicts (low-bandwidth use) |
| Vector DB | ✅ | pgvector (Supabase) | Guideline chunks + Rule Card embeddings (BGE-M3, 1024-d) |
| Object storage | ✅ | Supabase Storage (S3-compatible) | User uploads, generated reports; knowledge snapshots and lakehouse files |
| Data warehouse | ✅ | DuckDB | Analytics over lakehouse tables: evaluations, synthetic cohort, knowledge QA |
| Lakehouse | ✅ | Delta Lake (delta-rs), local files backed up to Supabase Storage | Bronze / silver / gold tables, with time travel for reproducible evaluations |
| Graph DB | ✅ | Neo4j AuraDB Free | Food Knowledge Graph + Personal Gut Graph |
| Cache / KV | ❌ *(Finals)* | Upstash Redis | LLM/VLM response cache, free-tier API rate-limit counters, recompute locks |

### 4.2 Schema design
**Postgres schemas**
- `core`: patient (pseudonymous ID only; identity stays in `auth.users`), profile (diagnosis, phenotype, stricture flag, disease state), medication, reminder
- `events`: meal_check (image ref, dishes JSONB, verdict, scores, evidence JSONB, model + prompt version), checkin (HBI/SCCAI items, weight, stress, sleep, doses taken), wearable_daily, lab_result (LOINC), verdict_feedback, red_flag_event
- `knowledge`: document, chunk (text, contextual header, embedding, tsvector, licence), rule_card
- `audit`: consent (scope, granted/revoked), access_log, model_run

**Neo4j graph model**
- `(Dish)-[:CONTAINS {typical_g}]->(Ingredient)-[:HAS_COMPONENT {per_100g, level}]->(Component)`
- `(Ingredient)-[:MAPS_TO]->(FoodCode)`: Bangladesh food table / USDA
- `(RuleCard)-[:ABOUT]->(Component)` · `(RuleCard)-[:APPLIES_TO]->(Phenotype|DiseaseState)` · `(RuleCard)-[:CITES]->(Paper)`
- `(Dish)-[:GENTLER_ALTERNATIVE]->(Dish)`
- `(Patient)-[:HAS_PHENOTYPE]->(Phenotype)` · `(Patient)-[:REACTS_TO {p, n, ci, updated_at}]->(Component|Dish)`
- Patient nodes hold a pseudonymous ID only; no health free-text in the graph

**Lakehouse layout (medallion)**
- Bronze: raw source snapshots and extraction outputs
- Silver: cleaned, normalised, entity-resolved foods, dishes, rules
- Gold: graph import tables, evaluation results, synthetic cohort features, differentially private research aggregates
- **No identifiable patient rows in the lakehouse**

**Redis keys**
- *(Finals; the prototype uses a Postgres `cache` table)* `cache:vlm:{sha256(image)}`: 7-day TTL
- `cache:llm:{prompt_hash}`: 24h TTL
- `cache:verdict:{patient}:{dish}:{profile_version}`: 1h TTL, invalidated when the graph updates
- `rl:{provider}`: token-bucket counters for free-tier quotas
- `lock:recompute:{patient}`

### 4.3 Partitioning
- Postgres: monthly range partitions on `meal_check`, `checkin` (`wearable_daily` in Finals)
- Delta bronze: partitioned by `source` / `ingest_date`
- Delta gold: evaluations by `eval_run`; synthetic cohort by `sim_run`
- Neo4j: population knowledge and per-patient subgraphs kept apart by label and ID

### 4.4 Indexes
- B-tree: `(patient_id, created_at DESC)` on all event tables
- GIN: JSONB dishes/evidence, tsvector full text
- pg_trgm trigram: Bangla and Banglish name search (Postgres has no Bangla stemmer)
- HNSW (pgvector, cosine, m=16, ef_construction=64): chunk embeddings
- BRIN: wearable timestamps *(Finals)*
- Partial index: unresolved red-flag events
- Neo4j: unique constraints on dish/ingredient/component IDs; full-text index on EN/BN names and aliases

### 4.5 Retention
- Meal photos: 30 days after extraction, unless the user chooses to keep them
- Voice notes: deleted right after transcription (transcript kept) *(Finals)*
- Health records: kept while the account is active; one-click export and delete, cascading across Postgres, the patient's Neo4j subgraph and storage
- LLM traces: 30 days, PII-scrubbed
- Audit and consent logs: 1 year
- Generated reports: signed URLs expire in 7 days
- Knowledge snapshots and synthetic data: kept permanently and versioned (synthetic data flagged)

### 4.6 Tiered storage
- Hot: Postgres, Neo4j, Redis (live app)
- Warm: Delta silver/gold tables, queried with DuckDB (analytics, evaluations)
- Cold: immutable bronze snapshots in Supabase Storage (reproducibility, licence audit)
- Edge: IndexedDB on the device (offline logging) *(Finals)*

### 4.7 Residency and operational notes
- Supabase region: Mumbai or Singapore (nearest to Bangladesh; no Bangladesh region exists)
- Encryption: AES-256 at rest (provider), TLS in transit, application-level encryption for free-text notes
- Free-tier limits (*check current values*): Supabase DB and storage caps; free Supabase projects pause when inactive, so keep the demo project warm before judging
- Free-tier limits (*check current values*): Aura Free node/relationship caps

## 5. Visualization and dashboards

### 5.1 Tools
| Tool | Select? | Role |
|---|---|---|
| Recharts | ✅ | Patient app charts (React) |
| D3.js | ✅ | Interactive Personal Gut Graph (d3-force via react-force-graph) |
| Plotly | ✅ | Evaluation-lab charts; static charts in the clinician PDF (Kaleido → PNG) |
| Streamlit | ✅ | Internal Model & Evaluation Lab |
| Grafana | ❌ *(Finals)* | Operations board over Postgres + Langfuse metrics |
| Metabase | ❌ *(Finals)* | Research dashboard over differentially private aggregates (Finals) |
| *Added:* Langfuse | ➖ used, listed under observability | LLM traces, token/cost, prompt versions, evaluation scores |
| *Added:* Neo4j Aura Explore | ➖ used, not ticked | Knowledge-graph curation and QA |
| *Added:* Mermaid | ➖ used, not ticked | Architecture and data-flow diagrams in docs |
| Chart.js, ECharts, Vega, Observable, Superset, Kibana, Dash | ❌ | Would duplicate the tools above |

### 5.2 Visualization details
**Patient app**
- Verdict card: 🟢🟡🔴⚪ icon + label + evidence bar (guideline / composition / personal contribution to the score)
- Symptom trend: HBI/SCCAI line with meal markers and dose ticks; 7 / 30 / 90-day toggle
- Trigger insights: per-component probability with credible interval (dot + whisker) and number of exposures
- Symptom-free-day calendar heatmap (custom SVG)
- Flare-risk gauge + top-factor waterfall (what pushed risk up or down)
- Wearable resting HR / HRV sparklines against a personal baseline band *(Finals)*
- Personal Gut Graph: patient → components → dishes; edge thickness = trigger probability; tap for evidence; the verdict path is highlighted

**Interactivity**
- Tap a data point → that day's meals and check-in
- Evidence tooltips on every score
- Range toggles
- Lazy-loaded graph view

**Real-time**
- Supabase Realtime pushes updated insights after each check-in and graph recompute
- Streamlit auto-refreshes during evaluation runs

**Accessibility and localization**
- Colour is never the only signal (icon + text on every verdict); colour-blind-safe palette
- WCAG AA contrast
- Bangla / English labels, optional Bangla numerals
- Screen-reader summary for every chart; one-line plain-language caption under each chart
- Low bandwidth: charts drawn client-side from small JSON; heavy libraries lazy-loaded
- Dark mode

### 5.3 Dashboards and reports
- Patient "My Gut" dashboard (in-app, Recharts + D3)
- Clinician pre-visit report: PDF (Bangla/English), shared by QR on demand + weekly n8n schedule
- Clinician read-only web view via expiring token link *(Finals)*
- Model & Evaluation Lab (Streamlit + Plotly), also used in the demo video's AI segment:
  - trigger-recovery precision/recall vs days of logging
  - verdict confusion matrix
  - flare-risk calibration
  - latency distribution
  - language/bias slices
- *(Finals)* Grafana ops board: p50/p90 latency, error rate, cache hit rate, free-tier quota burn
- Langfuse: traces, tokens, prompt-version comparisons, evaluation scores
- Nightly evaluation report (Markdown + charts) generated by n8n and committed to the repo
- Metabase research dashboard over differentially private aggregates, embedded in the admin page (Finals)
- Neo4j Aura Explore for knowledge-graph QA

## 6. ML, analytics and insights delivery

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
- Bias slices: Bangla vs English vs Banglish input, sex, disease phenotype
- Honesty: flare-model and trigger results are reported as results on simulated data

**Non-AI analytics**
- Verdict engine: deterministic weighted score (guideline severity × component level × disease-state multiplier + personal posterior) → 🟢🟡🔴 thresholds; low confidence → ⚪; unit-tested
- Hard overrides before any LLM output: stricturing Crohn's (insoluble fibre, skins, seeds, nuts → 🔴); red-flag symptoms → escalation
- Clinical indices: Harvey-Bradshaw Index and SCCAI computed from check-in items with standard published activity thresholds
- Early warning v0: rule score (index rise, blood, missed doses, weight loss past a threshold)
- Red-flag rule set: structured answers + Bangla/English/Banglish keyword patterns, run before the LLM
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
- Knowledge-gap loop: every ⚪ "Not sure" or unmatched dish is queued; an enrichment agent drafts graph facts → human review → graph update
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

---

## Decision log
| # | Decision | Why |
|---|---|---|
| DA1 | Guidance with non-open licences is used through team-authored Rule Cards with citations, not stored full text | Stays within licence while keeping every claim cited |
| DA2 | Don't tick "Third-party / Partner Data" | No partner agreements exist; the category points are already maxed |
| DA3 | Dish recognition uses a vision-language model; image datasets are for evaluation only | Free-tier budget, no time to train a vision model, and zero-shot VLMs handle new dishes |
| DA4 | Team-captured meal photos are the primary test set | Fully licensed, and genuinely Bangladeshi meals |
| DA5 | Synthetic data is always labelled; real longitudinal data (IBDMDB) only calibrates it | Rigour without fabricated results |
| DA6 | Portal ticks only for items that earn points **and** exist by Oct 31 (§0); the full design stays in §1–5 with Finals tags | Avoids overbuilding and claims we can't demo |
