# Step 3: Data lifecycle and engineering

> Status: **§1–4 drafted** (2026-09-24). Later sections are filled in as we work through the portal's data-lifecycle form.
> Rule (CLAUDE.md #8): every source is listed here with its licence **before** any code ingests it. Rows marked *verify* must be checked and updated before first ingestion.

**Tier legend:** **MVP** = needed for the hero flow by Oct 31 · **Finals** = Nov–Dec hardening · **Roadmap** = pitch only

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
| IoT / Sensor / Streaming | ✅ | Wearable heart rate, HRV, sleep and steps (import in MVP; live sync in Finals) |
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
| SYN-3 | **Bangla/Banglish evaluation utterances** | Generated with a local LLM, then reviewed by the team | Tests voice/text understanding and dish-name resolution | MVP |
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

HappyGut combines seven types of data source, each with a documented licence. Internal: our Supabase app database (patient profiles, meal checks, verdicts, daily check-ins using Harvey-Bradshaw Index and SCCAI items, medication adherence, and "was this right for you?" verdict feedback), the Neo4j Personal Gut Graph of learned tolerances, and team-authored Rule Cards that turn published IBD guidance into structured, cited rules. External free APIs: USDA FoodData Central (CC0 nutrient data), Open Food Facts (ODbL; barcode lookup of packaged foods sold in Bangladesh), Europe PMC (open-access IBD nutrition literature, filtered automatically by licence) and PubMed E-utilities (citation metadata so every claim links to a real paper). Public web: Wikipedia Bangladeshi cuisine pages in English and Bangla (CC BY-SA) for dish descriptions and ingredients, open-access ESPEN, IOIBD and AGA guideline documents, and the DGDA Bangladesh drug registry for local medicine brand names. Open datasets: the Food Composition Table for Bangladesh (INFS, University of Dhaka), Wikidata (CC0) for dish-ingredient relations and Bangla labels, published FODMAP composition tables, Google's Dakshina dataset for Banglish-to-Bangla transliteration, Mozilla Common Voice Bengali for speech evaluation, and IBDMDB public metadata for calibration. User uploads: meal, menu and label photos, Bangla/English voice notes, lab report photos, wearable export files, and a team-captured set of about 300 Bangladeshi meal photos used as our test set. Sensor data: heart rate, HRV, sleep and steps from wearables, imported from exports in the prototype and synced live via the Fitbit/Google Health APIs and Android Health Connect in the production roadmap. Synthetic data: a clearly labelled simulated cohort of IBD patients with known injected food triggers, used to measure how accurately our Trigger Discovery engine recovers them, plus generated and human-reviewed Bangla/Banglish, red-flag and guideline Q&A evaluation sets. We deliberately exclude proprietary databases (such as Monash FODMAP), social-media health posts and any real patient records.

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
| RSS / Atom Feeds | ✅ | PubMed saved-search and journal feeds for new IBD diet research (Finals) |
| Email Inbox | ❌ | Not needed |
| OCR | ✅ | Package labels, menus, lab reports, Bangladesh food-table PDF |
| Speech-to-Text | ✅ | Bangla/English/Banglish voice logging |

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
| XLSX | ✅ | Admin uploads (curated dish lists, portion tables) |
| PDF | ✅ | Guidelines, Bangladesh food table, lab reports; pre-visit report output |
| Parquet | ✅ | Lakehouse tables, synthetic cohort, evaluation results |
| Avro | ❌ | Not used |
| XML | ✅ | PubMed E-utilities, Europe PMC full text (JATS) |
| YAML | ✅ | Rule Cards (version-controlled), pipeline configuration |
| JSONL | ✅ | Open Food Facts dump, evaluation sets, LLM batch jobs |
| Markdown | ✅ | Crawled pages converted for RAG, prompt library |
| HTML | ✅ | Scraped pages (Wikipedia, guideline sites, DGDA) |
| Images | ✅ | Meal/label/menu photos, lab report photos |
| Audio | ✅ | Voice notes |
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
- PII scrub: Microsoft Presidio + local LLM (Bangla names, +8801 phone numbers, addresses); EXIF / GPS removed from photos
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
| NoSQL | ✅ | IndexedDB on the device (Dexie.js) | Offline-first queue of meal logs and check-ins, cached recent verdicts (low-bandwidth use) |
| Vector DB | ✅ | pgvector (Supabase) | Guideline chunks + Rule Card embeddings (BGE-M3, 1024-d) |
| Object storage | ✅ | Supabase Storage (S3-compatible) + Cloudflare R2 | User uploads, generated reports; knowledge snapshots and lakehouse files |
| Data warehouse | ✅ | DuckDB | Analytics over lakehouse tables: evaluations, synthetic cohort, knowledge QA |
| Lakehouse | ✅ | Delta Lake (delta-rs) on R2 | Bronze / silver / gold tables, with time travel for reproducible evaluations |
| Graph DB | ✅ | Neo4j AuraDB Free | Food Knowledge Graph + Personal Gut Graph |
| Cache / KV | ✅ | Upstash Redis | LLM/VLM response cache, free-tier API rate-limit counters, recompute locks |

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
- `cache:vlm:{sha256(image)}`: 7-day TTL
- `cache:llm:{prompt_hash}`: 24h TTL
- `cache:verdict:{patient}:{dish}:{profile_version}`: 1h TTL, invalidated when the graph updates
- `rl:{provider}`: token-bucket counters for free-tier quotas
- `lock:recompute:{patient}`

### 4.3 Partitioning
- Postgres: monthly range partitions on `meal_check`, `checkin`, `wearable_daily`
- Delta bronze: partitioned by `source` / `ingest_date`
- Delta gold: evaluations by `eval_run`; synthetic cohort by `sim_run`
- Neo4j: population knowledge and per-patient subgraphs kept apart by label and ID

### 4.4 Indexes
- B-tree: `(patient_id, created_at DESC)` on all event tables
- GIN: JSONB dishes/evidence, tsvector full text
- pg_trgm trigram: Bangla and Banglish name search (Postgres has no Bangla stemmer)
- HNSW (pgvector, cosine, m=16, ef_construction=64): chunk embeddings
- BRIN: wearable timestamps
- Partial index: unresolved red-flag events
- Neo4j: unique constraints on dish/ingredient/component IDs; full-text index on EN/BN names and aliases

### 4.5 Retention
- Meal photos: 30 days after extraction, unless the user chooses to keep them
- Voice notes: deleted right after transcription (transcript kept)
- Health records: kept while the account is active; one-click export and delete, cascading across Postgres, the patient's Neo4j subgraph and storage
- LLM traces: 30 days, PII-scrubbed
- Audit and consent logs: 1 year
- Generated reports: signed URLs expire in 7 days
- Knowledge snapshots and synthetic data: kept permanently and versioned (synthetic data flagged)

### 4.6 Tiered storage
- Hot: Postgres, Neo4j, Redis (live app)
- Warm: Delta silver/gold on R2, queried with DuckDB (analytics, evaluations)
- Cold: immutable bronze snapshots on R2 (reproducibility, licence audit)
- Edge: IndexedDB on the device (offline logging)

### 4.7 Residency and operational notes
- Supabase region: Mumbai or Singapore (nearest to Bangladesh; no Bangladesh region exists)
- Encryption: AES-256 at rest (provider), TLS in transit, application-level encryption for free-text notes
- Free-tier limits (*check current values*): Supabase DB and storage caps; free Supabase projects pause when inactive, so keep the demo project warm before judging
- Free-tier limits (*check current values*): Aura Free node/relationship caps; Upstash command quota; R2 free storage

## 5. Visualization and dashboards
_Pending._

## 6. ML, analytics and insights delivery
_Pending._

## 7. Orchestration, streaming and outbound APIs
_Pending._

## 8. Governance: privacy, quality, lineage, cost
_Pending._

---

## Decision log
| # | Decision | Why |
|---|---|---|
| DA1 | Guidance with non-open licences is used through team-authored Rule Cards with citations, not stored full text | Stays within licence while keeping every claim cited |
| DA2 | Don't tick "Third-party / Partner Data" | No partner agreements exist; the category points are already maxed |
| DA3 | Dish recognition uses a vision-language model; image datasets are for evaluation only | Free-tier budget, no time to train a vision model, and zero-shot VLMs handle new dishes |
| DA4 | Team-captured meal photos are the primary test set | Fully licensed, and genuinely Bangladeshi meals |
| DA5 | Synthetic data is always labelled; real longitudinal data (IBDMDB) only calibrates it | Rigour without fabricated results |
