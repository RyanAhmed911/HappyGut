# Preliminary submission scope (deadline Nov 20)

> **Rule:** the live demo and video only show things that really work. Every portal tick or claim must be **A** (real), **B** (real but minimal), or removed / reworded as planned (**C**). Updated 20 Nov 2026 against the code: hosting moved to Render, and items that were planned but not built are now marked **C**.
>
> **No paid services, no card details.** Every service below has a free tier that needs no card.

## 1. Free-only service register
| Service | Plan | Card? | Used for |
|---|---|---|---|
| Render | Free web service | No | FastAPI backend in Docker. Sleeps after 15 min without traffic; a free uptime ping (e.g. UptimeRobot) keeps it awake |
| Vercel | Hobby | No | Web app (PWA) and the `/docs` page |
| Gemini API | **Google AI Studio** key, free tier | No | Reading meal photos and text, explanations. AI Studio, **not** Google Cloud / Vertex. Free-tier data may be used by Google, so we send food photos and de-identified text only |
| Groq | Free | No | Fallback explanation model (gpt-oss-120b) |
| Langfuse Cloud | Hobby | No | Traces of meal checks (when keys are set) |
| GitHub | Free | No | Repository, Actions CI, pull requests |
| Supabase | Free | No | Migrations written and tested in CI; not live in the prototype |
| Ollama and other open-source tools | Self-hosted | No | Offline jobs on the team GPU (Ubuntu); the live app never uses it |
| YouTube, Facebook | Free | No | The same 180-second video on both |

**Not used:** Hugging Face Spaces (Docker Spaces now need a paid plan), Neo4j AuraDB, ngrok, Cloudflare Tunnel, Google Cloud / Vertex AI, AWS, paid domains, OpenAI / Anthropic APIs at runtime, Redis.

## 2. Submission items
| Item | Content | Owner |
|---|---|---|
| YouTube + Facebook video | 180 s: problem → solution → **real** demo → AI approach → impact (`video-script.md`) | Nusayba Mahfuza Zaman |
| Live / demo link | https://happygut-web.vercel.app with three test accounts (`test-credentials.md`); "How it works" at `/about`; pitch deck and technical documentation at `/docs` | Ryan Ahmed, Raiyan Rahman |
| GitHub repo | Code for the A/B tiers + docs, specs, prompt library; public before submission | Everyone |

## 3. Tier map
**A = real and working in the demo · B = real but minimal · C = not built (untick or reword as planned)**

### Product
| Feature | Tier |
|---|---|
| Meal check: photo / Bangla / English text → graded verdict + why + citations + alternative | **A** |
| Red-flag sentinel + escalation screen | **A** |
| Stricturing Crohn's hard rules | **A** |
| Nightly diary: day's foods (meals added from a check with one tap; any food or time can be edited), per-food reactions, stool (Bristol, blood, urgency), HBI / SCCAI, doses, notes | **A** |
| Sleep (bedtime, wake, quality, late-night flag) and stress (0–4, exam / stressful periods) | **A** |
| Flare Pattern Finder (Bayesian N-of-1 over food components, late / short sleep, stress, exam periods, missed doses) on the sample accounts | **A** |
| Remission / flare periods: timeline + separate Remission and Flare summaries | **A** |
| "My Gut" screen (trend, periods, weight, "My patterns") | **A** |
| Flare-risk outlook (rule-based v0) | **A** |
| Flare-risk outlook v1: LightGBM on the simulated cohort + SHAP drivers, shown beside v0 (ROC AUC 0.658 vs 0.558 on held-out simulated patients) | **A** |
| Clinician pre-visit report (print / save as PDF) | **A** |
| "How it works" page (flow, safeguards, data sources, measured results), open without sign-in at `/about` | **A** |
| Live `/docs` page: pitch deck + technical documentation with live system data; admin page to switch it on or off, schedule it and edit text, order and team | **A** |
| Food guide (every dish with the person's verdict) and meal ideas (dishes rated "likely OK"), computed by the engine | **A** |
| Sign-in with test accounts for judges (three patient types), restore-records action | **A** |
| Medicines and tests: own schedule, dose ticks, tests and appointments, reminders, in the diary and the doctor's report; no medicine advice | **A** |
| Weight tracking: weekly weigh-ins, trend, 30 / 90 / 180-day change, GLIM weight-loss notice, in the doctor's report | **A** |
| Health profile editing; verdicts change at once (stricture, lactose intolerance, IBS-like symptoms) | **A** |
| Personal Gut Graph view (SVG) | **A** |
| Reminders (browser notifications while the app is open or installed) | B |
| Real sign-up and storage for real users (Supabase Auth + Postgres) | **C** |
| LLM-written (generative) dietitian plans | **C** |
| Wearables, lab reports, voice | **C** |
| Federated learning, research portal | **C** |
| Figma prototype | **C** |

### Data lifecycle form (paste text: `data-lifecycle.md`)
| Item | Tier |
|---|---|
| Sources: internal, external APIs (Europe PMC, Gemini, Groq), user uploads (photos), synthetic | **A** |
| Sources: public web scraping, open datasets | **C** (untick) |
| Scrapy, Crawl4AI, Wikidata SPARQL | **C** (untick) |
| AI extraction: meal photo / label → JSON | **A** |
| AI extraction: LLM-drafted Rule Cards (25), reviewed by an LLM judge against retrieved quotes (not by clinicians) | **A** |
| Food-table PDF parsing, admin bulk upload | **C** (untick) |
| Postgres (Supabase migrations with row-level security, pg_trgm, pg_cron), tested in CI | B (not live) |
| pgvector, Neo4j, Supabase Storage / Realtime / webhooks | **C** (untick) |
| Delta, DuckDB, partitions in a lakehouse | **C** (untick) |
| Recharts | **A** |
| Streamlit, Plotly, D3, calendar heatmap, waterfall chart | **C** (untick) |
| Langfuse tracing: one trace per meal check with the model calls nested inside; photos and names never sent | **A** once the keys are set on Render |
| Rule engine, Bayesian statistics | **A** |
| LightGBM (flare-risk v1) | **A** |
| Anomaly z-score | **C** (untick) |
| n8n: health check, nightly refresh, weekly safety self-check, failure email (`n8n/workflows`) | **A** when running; otherwise "built, not deployed" |
| PII scrub (Bangladesh rules + Presidio), SSE streaming, REST API | **A** |
| ngrok, Cloudflare Tunnel | **C** (untick) |

### AI usage form (paste text: `ai-usage.md`)
| Item | Tier |
|---|---|
| Gemini (runtime), Groq gpt-oss-120b (fallback) | **A** |
| Gemma 3 12B on Ollama, BGE-M3 with sentence-transformers (offline GPU jobs) | **A** |
| Local Qwen3, Llama 3.1, DeepSeek-R1 | **C** (untick: never run) |
| Knowledge graph / Graph RAG over cited Rule Cards | **A** |
| Contextual RAG, semantic chunking, hybrid search, reranker, vector database | **C** (untick: no guideline corpus loaded) |
| MCP built: foodgraph, guidelines, evals, journal (12 read-only tools) | **A** |
| MCP built: research | **C** (untick) |
| MCP used: GitHub | **A** |
| MCP used: Neo4j, Filesystem, Playwright | **C** (untick) |
| MCP used: Supabase | Tick only if a teammate really connected it |
| Agent frameworks: LangGraph, Pydantic-AI | **A** |
| Agent frameworks: CrewAI, smolagents, DSPy | **C** (untick) |
| Fine-tuning | **C** (none; adaptation is prompt-level) |
| Eval: red-flag suite, simulated-cohort pattern recovery, verdict rules, dish names, flare-model test (`evals/RESULTS.md`, `evals/FLARE_MODEL.md`) | **A** |
| Eval: LLM judge (knowledge review), CI gate | **A** |
| Eval: dietitian-labelled verdict set, photo set, RAG ablation, Ragas, McNemar, Eval Lab | **C** (untick) |
| Guardrails (input + output) | **A** |
| Frontend builders: Claude Code | **A** |
| Frontend builders: Lovable, v0, Claude Artifacts, Gemini Canvas, Stitch | Tick only those a teammate really used |
| Workflow: LangGraph, n8n (4 workflows), GitHub Actions CI | **A** |
| AI-DLC: AGENTS.md, Spec-Kit, Claude Skills | **A** |
| Model card (flare model) | **A** |
| `/docs` module | **A** |

## 4. Reconciliation checklist (before submitting)
- [ ] Untick every **C** item above in the portal; paste the text from `ai-usage.md`, `data-lifecycle.md` and `provenance.md`
- [ ] Hosting everywhere says Render + Vercel (not Hugging Face Spaces)
- [ ] Set on Render: `DEMO_MODE`, the three `TEST_PASSWORD_*`, `SESSION_SECRET`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `CORS_ORIGINS`, `PORT=7860`, `DOCS_ADMIN_PASSWORD`; optional `LANGFUSE_*`, `JOBS_TOKEN`
- [ ] Sign in with all three test accounts on the live link; check `/docs` and `/about` open without sign-in
- [ ] Say that evaluation results come from a simulated cohort in the video, /docs, README and portal; the app shows its sample-data notice once at entry
- [ ] Describe knowledge review as "LLM judge against published sources", never as clinical review
- [ ] Roles declared (portal, `/docs`, `one-page-summary.md`, `TEAM-HANDOVER.md`)
- [ ] Make the repo public; check no keys are in git history (GitGuardian has passed on every pull request)
