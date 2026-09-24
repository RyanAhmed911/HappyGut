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
