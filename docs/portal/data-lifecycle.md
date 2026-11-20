# Portal text: Data lifecycle (prototype, updated 20 Nov)

> Paste-ready lists for the portal's "Data Lifecycle & Engineering" page. **List only what is really used.** Every line was checked against the code on 20 Nov 2026. Source register and licences: `docs/03-data.md`.

## 1. Data sources (tick)
- ✅ Internal (own DB / app data)
- ✅ External APIs (Europe PMC for sources; Gemini and Groq)
- ✅ User uploads (meal photos; no bulk import)
- ✅ Synthetic / AI-generated data
- ❌ Not used: public web scraping, open datasets, IoT / streaming, third-party data

Synthetic data text box:
```
Simulated IBD patient cohort: 200 patients × 120 days of diaries with known hidden contributors (food components, late nights, stress, exam periods, missed doses), used to evaluate the Pattern Finder and train the LightGBM flare model
Red-flag test suite: 29 emergency phrases and 30 ordinary messages in English, Bangla and Bangla typed in English letters (written by the team)
Three sample patient accounts for the demo, labelled as sample data
```

## 2. Acquisition (tick)
- ✅ AI extraction, ✅ MCP servers for data access, ✅ automated flows (n8n workflows and LangGraph), ✅ API pull / SDK
- ❌ Not used: web scrapers, bulk upload, RSS, email parsing, OCR tools, speech-to-text

Scrapers / crawlers used:
```
None. Dishes and Rule Cards were written from published, licensed sources (each paper confirmed by DOI / PMID through the Europe PMC API) and checked by an LLM judge.
```

MCP servers for data access:
```
Built (4, read-only): happygut-foodgraph (search_dish, get_components, explain_verdict_path), happygut-guidelines (cited Rule Cards), happygut-evals (measured results, red-flag check), happygut-journal (one patient's own records, with their sign-in)
Used in development: GitHub MCP
```

Pipeline:
```
Meal photo or text → Gemini returns dishes as JSON, validated against a Pydantic schema → dish resolver over Bangla, English and English-letter names
Guideline paper (open access, DOI/PMID confirmed via Europe PMC) → LLM drafts a Rule Card → LLM judge checks it against the exact retrieved sentence → approved YAML seed
Dish YAML seeds → validator (every dish has ingredients, component levels, sources) → knowledge graph
Low confidence or no evidence → ⚪ "Not sure"
```

## 3. Parsing, formats and cleaning
Formats: ✅ JSON, ✅ CSV, ✅ YAML, ✅ JSONL, ✅ Images. ❌ PDF (we don't parse PDFs; the doctor's report is printed to PDF by the browser).

Parsers used:
```
PyYAML: dish and Rule Card seeds, versioned prompt files
Pydantic v2: Gemini JSON output, API requests, diary entries
Pillow: image check, downscale, EXIF/GPS strip
Presidio + spaCy (en_core_web_sm): name detection inside the PII scrub
```

Formatters / converters:
```
React report page → browser "Print / Save as PDF" (clinician pre-visit summary)
Evaluation run → Markdown report (evals/RESULTS.md) + JSON summary shown in the app
/docs page → Markdown download and print to PDF
```

Data cleaning & enrichment:
```
Personal details removed before any cloud AI call: Bangladesh-specific rules (names after self-introduction, +880 phone numbers, NID / birth-registration numbers, emails, links) plus Microsoft Presidio
Photos: type and size checked, downscaled, re-encoded as JPEG with all EXIF / GPS data removed; never stored
Dish names: fuzzy matching over Bangla, English and English-letter spellings; 50 extra spellings suggested by a local model (Gemma 3 12B) and accepted by an LLM judge, 87 rejected
Enrichment: each dish → ingredients → gut-relevant component levels → the Rule Cards that apply to this patient's diagnosis and state
Diary answers turned into the Harvey-Bradshaw Index (Crohn's) or SCCAI (colitis), sleep hours and a late-night flag; meal times set the time of day
Times stored in UTC and shown in Asia/Dhaka
```

Schema validation:
```
Pydantic v2: every API request, diary entry and model output (Gemini's dishes JSON is rejected and retried if it doesn't match the schema)
Zod: every API response checked in the web app before it's shown
Seed validator: every dish and Rule Card file checked on each pull request (required fields, allowed component levels, valid source and review fields)
Business rules: times as HH:MM, no future days, diary edits only for recent days, limits on foods per day and medicines per patient
Each prompt file declares the output schema its answer must match
```

## 4. Storage (tick)
- ✅ Relational (Postgres): reworded below
- ❌ Vector DB, data warehouse, lakehouse, graph DB, object storage, cache / KV

Storage text box:
```
Knowledge: 109 dishes and 25 Rule Cards as reviewed YAML files in git, loaded into an in-memory knowledge graph at start-up
Prototype demo: the three sample accounts' records are kept in memory and can be reset (Restore original records)
Supabase Postgres prepared for real users: schema, row-level security, Bangla fuzzy search (pg_trgm), consent and audit tables, monthly partitions and scheduled clean-up (pg_cron); written as migrations and tested in CI, not yet live
Evaluation results (JSON + Markdown) and the LightGBM model file with its model card versioned in git
No photos and no real patient data stored
```

## 5. Visualization (tick)
- ✅ Recharts
- ❌ Not used: D3.js, Plotly, Streamlit and the rest (other charts are hand-written SVG)

Visualization details:
```
Verdict card: 🟢 🟡 🔴 ⚪ icon + colour + label (never colour alone), confidence, two evidence bars (IBD guidance / your own diary), a gentler-option chip, and "Why? See the evidence" opening the rule, its quoted sentence and DOI / PMID
Meal banner showing the overall verdict above the dish cards
HBI / SCCAI trend line (Recharts) with flare periods shaded and the activity threshold marked; 30 / 90 days / all toggle
Period timeline bar: remission, flare and settling periods in sequence
Flare-risk gauge (0–100, SVG) with each reason and its points; below it, the machine-learning estimate with its top three SHAP drivers
Personal Gut Graph (SVG): the patient in the centre, linked foods and habits around them, coloured by strength of the link
Pattern cards: "after this" vs "other days" bars with exact counts (e.g. 11 / 14 vs 37 / 101)
Weight chart with 30 / 90 / 180-day change; Bristol stool chart pictures in the diary
Architecture and data-flow diagrams on the /docs page
Mobile-first, every chart and label in Bangla and English, with Bangla numerals in Bangla
```

Dashboards & reports:
```
My Gut: HBI / SCCAI trend with flare periods shaded, remission vs flare summaries, weight chart with 30 / 90 / 180-day change
My patterns: Personal Gut Graph and one card per pattern with its counts ("followed by a worse day 11 of 14 times")
Today: flare-risk gauge with its top reasons and the machine-learning estimate with SHAP drivers
Doctor's pre-visit report: one page, printable or saved as PDF
/docs: live system dashboard (feature status, API endpoints, knowledge counts, models in use, usage counts) with the pitch deck and technical documentation
"How it works" page and evals/RESULTS.md: measured results of each evaluation run
Langfuse: one trace per meal check (steps, timings, model calls), when the keys are set
```

## 6. Insights: AI, ML and non-AI (tick)
- ✅ Classical ML (LightGBM), ✅ LLM inference (over the knowledge graph), ✅ Rule engine, ✅ Statistical analysis (Bayesian)
- ❌ Not used: anomaly detection, deep learning, forecasting libraries, clustering

AI / ML details:
```
Perception: Gemini (flash-lite, falling back to flash) reads the photo or text → dishes as JSON, validated against a Pydantic schema; typed dish names are matched locally without a model call
Graph retrieval: in-memory knowledge graph built from reviewed YAML seeds: Dish → ingredients → gut-relevant components (levels) → Rule Cards for the patient's diagnosis and state → paper (DOI/PMID) and its exact quoted sentence
Verdict: deterministic, unit-tested engine; stricture rules apply first; no evidence → ⚪ "Not sure"
Explanation: Gemini writes the "why" in Bangla or English only from the engine's verdict and the retrieved evidence (Groq gpt-oss-120b as fallback); a guard compares the text with the verdict and shows a template on mismatch
Flare Pattern Finder: Bayesian N-of-1 per patient and factor (high-level food components, late nights, short or poor sleep, high stress, exam and other stressful periods, missed doses)
Pattern Finder: a "worse day" is ≥ 2 index points above the person's own 14-day median; it compares how often worse days follow a factor (food: same day or next, ≈6–48 h) with days without it
Pattern Finder: Beta–Binomial posteriors (sceptical prior for the factor), P(rate after the factor > rate without it + 10 points) by seeded Monte Carlo, with a 90% interval
Pattern Finder: "likely contributor" at P > 0.8 with ≥ 3 exposures; factors that usually occur together are shown as "often happens together with"; always "linked to", never "caused"
Flare-risk v1: LightGBM predicting whether a flare starts within the next 3 days, shown beside the rule-based score v0
Flare features (24, no look-ahead): HBI/SCCAI today, 3-day mean, 7-day max, rise and slope, active and logged days, food reactions, late nights, short and poor sleep, stress, stressful period now or soon, missed doses, high-level food exposures, flare days in the last 30, days since the last flare
Flare training: patients split, never days (100 train, 50 validation to pick the number of trees, 50 held out); SHAP top 3 drivers shown with each estimate
Training data: simulated IBD cohort, 200 patients × 120 days with known hidden contributors, labelled synthetic
Test data: held-out simulated patients; red-flag suite (29 emergency phrases, 30 ordinary messages, team-written); 109 dishes × 7 patient profiles for verdict checks; every stored dish name and spelling
Metrics, Pattern Finder: hidden contributors found and false reports at 21/30/60/90/120 days (120 days: 274 of 400 found, 68%; 71 false reports)
Metrics, flare model: ROC AUC 0.658 vs 0.558 for the rule score; average precision 0.077 vs 0.031; Brier 0.0193; flagging the top 10% of days catches 30 of 98 flare starts vs 11
Metrics, safety and engine: red-flag recall 29/29 with 0/30 false alarms; 763/763 verdicts identical on repeat; stricture rule 19/19; engine 0.16 ms per three-dish meal
Results by language: red flags reported separately for English, Bangla and Bangla in English letters
All flare and pattern results are on simulated data, not real patients
Next (not built yet): vector search over guideline text, photo-recognition accuracy on a licensed photo set, agreement with a dietitian-labelled verdict set
```

Non-AI analytics:
```
Verdict engine (deterministic, unit-tested): for each dish component, risk = the higher of the guideline score (rule severity × component level × disease-state multiplier) and the patient's own pattern score
Hard rules first: stricturing Crohn's rules (insoluble fibre, skins, seeds, nuts) make a dish 🔴 before anything else runs
Thresholds turn risk into 🟢 Likely OK / 🟡 Caution / 🔴 Likely trigger; evidence coverage below 50% → ⚪ Not sure; the meal shows its worst dish; a gentler alternative is picked from the knowledge graph
Red-flag sentinel: rule-based detection of emergency phrases in English, Bangla and Bangla in English letters
Disease indices from the diary: Harvey-Bradshaw Index (Crohn's) and SCCAI (colitis)
Remission / flare periods: a flare is proposed when the index is active on 3 of 4 consecutive days and ends after 7 calm logged days; the patient confirms or rejects it
Flare-risk outlook v0: a transparent score where every point comes from a named reason (index rising, poor sleep, missed doses, a stressful period starting soon, linked foods)
Flare Pattern Finder: Bayesian statistics per patient (Beta–Binomial, ≥ 3 exposures, "linked to", never "caused")
Weight: change over 30 / 90 / 180 days and the GLIM weight-loss threshold (> 5% in 6 months, > 10% beyond)
Sleep hours and a late-night flag against the person's usual bedtime; medicine doses due from each schedule
```

How are insights delivered to users?
```
Verdict card right after each check, streamed step by step: verdict, why, citations and a gentler option, in Bangla or English
Red-flag escalation screen instead of any food advice when a warning sign is reported
Today screen: upcoming stressful periods, flare-risk card, today's doses with "Mark taken", the next test
My Gut and My patterns screens; weight-loss notice to tell the doctor (GLIM threshold)
Browser notifications (while the app is open or installed): medicine, test and nightly-diary reminders
Doctor's pre-visit report to take to the next visit
```

## 7. Pipelines and orchestration
Orchestration:
```
LangGraph: the meal-check flow (red-flag check → PII scrub → perception → engine → explanation)
n8n (Docker, 4 workflows): health check, nightly refresh, weekly safety self-check, failure alert email
```
Scheduling / triggers:
```
n8n: health check every 30 min; nightly refresh 23:30; safety self-check Mondays 07:10
In-app reminders for medicines, tests and the nightly diary
```
Streaming / real-time:
```
Server-Sent Events: each meal check streams its steps and verdicts to the phone as they're computed
```

## 8. Outbound: APIs and distribution
Outbound APIs:
```
FastAPI REST, versioned /v1: POST /v1/meal-checks (SSE), POST /v1/meal-checks/{id}/diary, GET/PUT /v1/diary/{day}, GET /v1/insights/patterns, /v1/insights/periods, /v1/insights/flare-risk, /v1/reports/previsit, /v1/weights, /v1/medications, /v1/appointments, GET /v1/docs (live documentation data)
The full endpoint list is generated from the running API on the /docs page
```
Webhooks & exports:
```
Doctor's pre-visit report: printable, or saved as PDF from the browser
/docs: Markdown download and print to PDF
n8n calls two protected job endpoints (nightly refresh, weekly safety self-check) with a bearer token, and emails an alert if a workflow fails
MCP servers (read-only): food knowledge, cited Rule Cards and evaluation results for AI clients; a patient's own records for their AI assistant, using their own sign-in
Evaluation results exported as JSON to the app's "How it works" page
```
Embeddings / model serving:
```
Ollama on the team GPU for offline jobs only: Gemma 3 12B (spelling variants), BGE-M3 (dish embeddings); the live app uses the Gemini and Groq APIs
LightGBM model file served inside the FastAPI backend
```

## 9. Open-source stack
```
FastAPI, Pydantic v2, LangGraph, Pydantic-AI: backend and meal-check flow
Presidio + spaCy: PII detection
LightGBM: flare-risk model
React, Vite, Tailwind, TanStack Query, Zod, Recharts, react-i18next: web app (Bangla + English)
PostgreSQL + pg_trgm + pg_cron (Supabase migrations), PGlite for database tests
n8n: scheduled workflows; Ollama: offline GPU jobs
MCP Python SDK: 4 read-only MCP servers
pytest, Vitest, GitHub Actions: tests on every pull request
```

## 10. Quality, governance and observability
Data quality:
```
Seed validator on every pull request: each dish has ingredients, component levels and sources; each Rule Card has a DOI / PMID-confirmed paper and an exact retrieved sentence
LLM-judge review of every dish, Rule Card, spelling and Bangla string against published sources (not clinical review)
Every stored dish name and spelling resolves to its own dish (Bangla 109/109, English 109/109, other spellings 477/477)
Patterns need ≥ 3 exposures and 7 baseline days, otherwise "not enough data"; the flare model waits for 14 days of diary
Red-flag suite (29 / 29 caught, 0 / 30 false alarms) and 763 / 763 reproducible verdicts re-checked by a deterministic evaluation run
CI tests on engine, backend, MCP servers, seeds, web app and database on every pull request
```
Privacy & compliance:
```
Prototype holds no real patient data: three sample accounts, labelled as sample data once at entry; evaluation uses a labelled simulated cohort
Personal details removed inside our backend before any cloud AI call: Bangladesh-specific rules (names after self-introduction, +880 phone numbers, NID / birth-registration numbers, emails, links) plus Microsoft Presidio
Photos are never stored: type and size checked, location and other EXIF data stripped, read once, then discarded; the app never asks for location
Only free-tier AI services, sent food photos and de-identified text only; no medication advice and no diagnosis
HTTPS everywhere (Render and Vercel); sign-in tokens signed by the backend; failed-login lockout
Self-management support, not a medical device; disclaimer on every screen in Bangla and English
Prepared for real users (database migrations written and tested in CI, not yet live): row-level security on every patient table, revocable consent records per purpose, audit log
Next: patient data export and deletion, consent screens, research outputs as aggregates only with small groups suppressed; built to GDPR principles and Bangladesh data-protection requirements
```
Lineage & observability:
```
Every dish and Rule Card records its sources, licence and review (method, date, verdict); licences listed in docs/03-data.md
Every Rule Card links to its paper (DOI / PMID) and the exact sentence retrieved from Europe PMC
Every verdict records the engine version, the perception and explanation prompt versions and the models used
Offline GPU jobs record the model, its digest and the git commit they ran on
Flare model card: training date, data, features, split and metrics; retraining is one deterministic command
Langfuse traces each meal check (steps, timings, model calls), with names and photos never sent
```
Cost & performance:
```
Running cost $0: free tiers with no card (Gemini via Google AI Studio, Groq, Render, Vercel, Langfuse Hobby, GitHub); the team GPU only for offline jobs
At most 2 model calls per meal check; typed dish names need none; the verdict engine itself takes 0.16 ms per three-dish meal
Small model first (Gemini flash-lite), larger model and a second provider (Groq) only as fallback; a template explanation if every quota runs out
Backend peaks at about 260 MB in memory, within the 512 MB free server; the LightGBM model runs inside it with no extra service
```

## 11. Anything else about your data stack?
```
AI-native but safety-first: the LLM only reads the plate and explains; a deterministic, unit-tested engine makes every verdict, and red flags stop food advice before any AI runs. Live documentation with system data at /docs. Next: load the knowledge into Neo4j and pgvector, real sign-up with Supabase, and a consented pilot to replace simulated data.
```

## 12. Publishing local environment to the internet
- ❌ Untick ngrok and Cloudflare Tunnel
```
None used. The live app runs on Render (backend) and Vercel (web app); the team GPU only runs offline jobs and exchanges files through git.
```
