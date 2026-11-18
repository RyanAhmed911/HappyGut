# Preliminary submission scope (submit Nov 19; deadline Nov 20)

> **Rule:** the live demo and video only show things that really work. The Figma prototype shows the full vision. Before submitting, every portal tick or claim must be **A** (real), **B** (real but minimal), or removed / reworded as planned (**C**).
>
> **No paid services, no card details.** Every service below has a free tier that needs no card.

## 1. Free-only service register
| Service | Plan | Card? | Notes |
|---|---|---|---|
| Supabase | Free | No | Postgres + pgvector + Auth + Storage + Realtime. Small DB/storage caps; **pauses after ~1 week idle**, so keep it active before judging |
| Neo4j AuraDB | Free | No | Node/relationship caps; pauses when idle (*check current terms*) |
| Gemini API | **Google AI Studio** key, free tier | No | Use AI Studio, **not** Google Cloud / Vertex. Rate-limited; free-tier data may be used by Google, so we send food photos + de-identified text only |
| Groq | Free | No | Rate-limited |
| Hugging Face Spaces | CPU Basic | No | Always-on runtime: FastAPI backend (incl. embeddings, reranker, foodgraph MCP) and n8n (workflows stored in Supabase). Spaces sleep after ~48 h without traffic, so a scheduled GitHub Actions ping keeps them awake |
| Vercel | Hobby | No | Frontend PWA |
| ngrok | Free | No | Dev webhooks; one free static domain |
| Langfuse Cloud | Hobby | No | Tracing + eval scores |
| GitHub | Free, public repo | No | Repo, Actions CI, issues/PRs |
| Ollama, all OSS libraries | Self-hosted | No | Ollama runs finite GPU jobs on the team GPU (Ubuntu); the live app never uses it |
| USDA FoodData Central, NCBI | Free API keys | No | |
| Figma, Lovable, v0, Google Stitch | Free tiers | No | Lovable/v0 have daily credit limits, so plan UI generation |
| YouTube, Facebook | Free | No | Same 180s video on both |

**Not used:** Google Cloud / Vertex AI, AWS, Cloudflare R2, paid domains, OpenAI / Anthropic APIs at runtime, Redis/Upstash.

## 2. Submission items
| Item | Content | Owner |
|---|---|---|
| YouTube + Facebook video | 180s: problem → solution → **real** demo → AI approach (architecture + Eval Lab numbers) → impact | Presentation lead |
| Live / demo link | Deployed PWA + three test accounts ([`test-credentials.md`](test-credentials.md)) + the in-app "How it works" page | Frontend + backend |
| GitHub repo | Code for the A/B tiers + docs, specs, prompt library; public before submission | Everyone |
| Figma / design | Clickable prototype of the **full vision** (incl. C features, labelled "design prototype") | UI/UX |

## 3. Tier map
**A = real and working in the demo · B = real but minimal · C = design/roadmap only (untick or reword before submitting)**

### Product
| Feature | Tier |
|---|---|
| Meal check: photo / Bangla / English text → graded verdict + why + citations + alternative | **A** |
| Red-flag sentinel + escalation screen | **A** |
| Stricturing Crohn's hard rules | **A** |
| Nightly diary: day's foods (pre-filled from meal checks), per-food reactions, stool (Bristol, blood, urgency), HBI / SCCAI, doses, notes | **A** |
| Sleep (bedtime, wake, quality, late-night flag) and stress (0–4, exam / stressful periods) | **A** |
| Flare Pattern Finder (Bayesian N-of-1 over food components, late / short sleep, stress, exam periods, missed doses) on the simulated demo persona | **A** |
| Remission / flare periods: timeline + separate Remission and Flare summaries | **A** |
| "My Gut" screen (trend, periods, "My patterns") | **A** |
| Flare-risk outlook (rule-based v0) | **A** |
| Flare-risk outlook v1: LightGBM on the simulated cohort + SHAP drivers | B |
| Clinician pre-visit PDF | B |
| "How it works" page (flow, safeguards, data sources, measured results), open without sign-in at `/about` | **A** |
| Reminders (web push) | B |
| Food guide (every dish with the person's verdict) and Meal ideas (a week from dishes rated "likely OK"), computed by the engine | **A** |
| Sign-in with test accounts for judges (three patient types), restore-records action | **A** |
| Medicines and tests: the patient's own medicine schedule with dose ticks, tests and appointments, reminders on the phone (while the app is open or installed), in the diary and the doctor's report; no medicine advice | **A** |
| Weight tracking: weekly weigh-ins, trend, change over 30 / 90 / 180 days, a notice to tell the doctor past the GLIM weight-loss threshold, in the doctor's report | **A** |
| Health profile editing; verdicts change at once (stricture, lactose intolerance, IBS-like symptoms) | **A** |
| Personal Gut Graph view (SVG) | **A** |
| Diary reminder notification (while the app is open or installed) | B |
| LLM-written (generative) dietitian plans | **C** |
| Wearables, lab reports, voice | **C** |
| Federated learning, research portal | **C** |

### Data lifecycle form
| Item | Tier |
|---|---|
| Sources: Internal, APIs, Public web, Open datasets, Uploads, Synthetic | A |
| Scrapy (Wikipedia, ~50 dishes), Crawl4AI (guideline pages), Wikidata SPARQL | A |
| AI extraction: meal photo / label → JSON | A |
| AI extraction: LLM-drafted Rule Cards (25), reviewed by an LLM judge against retrieved quotes (not by clinicians) | A |
| Food-table PDF parsing (subset of foods) | B |
| Admin bulk upload | B |
| Postgres, pgvector, Supabase Storage, Neo4j | A |
| Delta + DuckDB (evaluation results, synthetic cohort) | B |
| Partitions, retention job | B |
| Recharts, Streamlit + Plotly | A |
| D3, Langfuse dashboards | B |
| Calendar heatmap, waterfall chart | B (drop if short on time) |
| Rule engine, Bayesian statistics | A |
| Anomaly z-score, LightGBM | B |
| n8n (reminders, nightly), Supabase webhooks, Realtime, exports, GitHub Actions gate | B |
| PII scrub (Presidio + Gemma), row-level security, SSE streaming, REST API | A |
| ngrok | B |

### AI usage form
| Item | Tier |
|---|---|
| Gemini, Transformers (BGE-M3, reranker, Bengali NER on CPU) | A |
| Ollama | A (GPU jobs) |
| Groq Llama | A |
| Local Qwen3 14B, Gemma 3 12B, Llama 3.1 8B, DeepSeek-R1 8B (Qwen3-based distill) (GPU jobs on Ubuntu) | A |
| RAG: contextual, semantic chunking, Graph RAG, KG, hybrid, reranker | A |
| MCP built: foodgraph | A |
| MCP built: guidelines, evals, journal | B |
| MCP built: research | B (thin, synthetic aggregates). If not built → remove (4 built = 8/10) |
| MCP used: Supabase, Neo4j | A |
| MCP used: Filesystem, GitHub, Playwright | B |
| Agent frameworks: LangGraph, Pydantic-AI | A |
| Agent frameworks: CrewAI, smolagents, DSPy | **C**: untick unless built |
| Fine-tuning (embedding) | **C**: keep only the "prompt-level adaptation" lines unless done |
| Eval: red-flag suite, simulated-cohort pattern recovery, verdict rules, dish names (`evals/RESULTS.md`) | A |
| Eval: dietitian-labelled verdict set, RAG ablation, Eval Lab | **C**: not built; untick or build |
| Eval: LLM judge, 50-sample human eval, McNemar, CI gate | B |
| Guardrails (input + output) | A |
| Frontend builders: Lovable | A |
| Frontend builders: v0, Claude Artifacts, Gemini Canvas, Stitch | B (tick only those really used) |
| Workflow: LangGraph | A |
| Workflow: n8n, GitHub Actions, Supabase webhooks | B |
| AI-DLC: AGENTS.md, Spec-Kit, Claude Skills | A (set up on day 0) |
| Model / data cards | B |

## 4. Reconciliation checklist (Nov 19, before submitting)
- [ ] Untick every C item that wasn't built (CrewAI, smolagents, DSPy, fine-tune, research MCP if missing)
- [ ] Replace estimates with real numbers: % AI-built UI, MCP endpoints called, eval metrics
- [ ] Fill in versions and URLs: exact model versions, repo / deploy URLs
- [ ] Re-paste any portal text changed since it was first entered (see git history of `docs/portal/`)
- [ ] Say that evaluation results come from a simulated cohort in the video, /docs, README and portal; the app shows its sample-data notice once at entry
- [ ] Describe knowledge review as "LLM judge against published sources", never as clinical review
- [ ] Make the repo public; check no keys are in git history
- [ ] Add the real build prompts to the prompt library
