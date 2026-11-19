# HappyGut Roadmap: from plan to finals

> Living document. Tick steps off as they finish. Dates are targets. **Fixed dates (AIBC Participants Guide):** team preliminary submission closes **20 Nov 2026**, selection announced **25 Nov**, finals **26 Dec**. We submit a day early, on **19 Nov**.

## Planning and design steps

| Step | Window | Output | Status |
|---|---|---|---|
| **1. Strategy & scope** | Sep 24–27 | [`01-strategy.md`](01-strategy.md): stress test, positioning, hero flow, scope tiers, KPIs, rubric map | 🟡 Draft, awaiting team review |
| **2. Architecture & stack** | Oct 21 | [`02-architecture.md`](02-architecture.md): system, hero-flow sequence, verdict engine, repo layout, decisions | ✅ v1.0 |
| **3. Data & knowledge design** | Sep 29–Oct 3 | [`03-data.md`](03-data.md): sources and licences, scrapers/parsers, Food KG schema, guideline corpus, synthetic cohort spec, data lifecycle, privacy | ✅ Drafted (§1–10) |
| **4. UX & Bangla design** | Sep 29–Oct 3 | `04-ux.md` + Figma: hero-flow screens, verdict card, check-in, Bangla copy, low-bandwidth rules | ⏳ |
| **5. Evaluation & safety plan** | Oct 1–4 | `05-evaluation.md`: test sets, metrics, red-flag suite, bias slices | ⏳ |

## Build plan (Nov 7 → Nov 19)
Scope = tiers A and B in [`portal/submission-scope.md`](portal/submission-scope.md). Architecture: [`02-architecture.md`](02-architecture.md). Rules: [`../.specify/memory/constitution.md`](../.specify/memory/constitution.md). Scope changes of 2026-11-07 (Bangla + English only, nightly diary, sleep, stress, Flare Pattern Finder, remission / flare periods): [`01-strategy.md`](01-strategy.md) §12.

| Day | Step | Spec | Done means | Status |
|---|---|---|---|---|
| Oct 21 | **0. Foundation** | — | Accounts ready, dev setup on Windows ([`setup.md`](setup.md)); skeleton, constitution, AGENTS.md, skills, specs 001–002 pushed | ✅ Accounts created (2026-11-07); keys go in `.env` on Windows |
| Nov 7–9 | **1. Knowledge layer** | [001](../specs/001-knowledge-layer/spec.md) | Demo dishes + stricture Rule Cards approved first, then the rest; loader (T013) puts them in Neo4j + pgvector; foodgraph MCP | 🟡 109 dishes (61 on 2026-11-15, 48 fast-food, snack, drink and fruit dishes on 2026-11-19) and 25 Rule Cards approved by the LLM judge ( every Rule Card has an exact retrieved quote); 50 spellings added. Graph, schema, MCP and GPU jobs G2/G3 done. Open: loader to Neo4j / Supabase, guideline corpus, rerun G3 for the new spellings |
| Nov 9–11 | **2. Hero flow** | [002](../specs/002-meal-check/spec.md) | Photo/text (Bangla or English) → Bangla verdict card with citations, end to end on a phone | 🟡 Backend and PWA built and working in demo mode (typed meals; photos need the Gemini key). Photo checks confirmed working with the team's keys (2026-11-15); sign-in with three test accounts. Next: deployment |
| Nov 11–14 | **3. Personal layer** | [003](../specs/003-personal-layer/spec.md) | Nightly diary (foods, reactions, stool, HBI/SCCAI, sleep, stress, doses), stressful periods, simulated cohort + demo persona, Flare Pattern Finder, remission / flare timeline and tabs, flare-risk v0, "My Gut" | 🟡 Built and working in demo mode on the simulated persona: nightly diary, sleep, stress, stressful periods, Flare Pattern Finder, remission / flare periods, flare-risk v0, doctor's report. Open: Postgres storage for the diary, web push, simulated cohort (200 patients) |
| Nov 14–15 | **4. Proof** | 004 | Eval sets, red-flag suite, trigger / pattern recovery on the simulated cohort, LightGBM + SHAP outlook (B), RAG ablation, Eval Lab | 🟡 Measured on 2026-11-17 ([`../evals/RESULTS.md`](../evals/RESULTS.md)): Pattern Finder on 200 simulated patients, red-flag suite by language, verdict rules, dish names. LightGBM flare-risk v1 trained and evaluated (2026-11-18, [`../evals/FLARE_MODEL.md`](../evals/FLARE_MODEL.md)). Open: photo accuracy, dietitian-labelled verdict set, RAG ablation |
| Nov 16–17 | **5. Ship** | — | Deployed URL, demo account, /docs, clinician PDF, Figma prototype | ⏳ |
| Nov 18 | **6. Video** | — | 180s video on YouTube + Facebook, 1-page summary | 🟡 Script: [`portal/video-script.md`](portal/video-script.md); summary draft: [`portal/one-page-summary.md`](portal/one-page-summary.md). Recording is open |
| Nov 19 | **7. Reconcile & submit** | — | Checklist in `portal/submission-scope.md` §4 done; submitted a day early | ⏳ |

**Cut order if behind:** smolagents → CrewAI → DSPy → embedding fine-tune → research MCP → dietitian agent → LightGBM outlook (keep the Bayesian Pattern Finder) → per-period patterns (keep the period timeline). Never cut: hero flow, nightly diary, evals, video.

## Proposed role mapping (fill in names: mandatory, see [`portal/guide-checklist.md`](portal/guide-checklist.md))

The team works across everything, but the portal needs named owners. This mapping gives each role the workstream it naturally leads.

| Official role | Name | Leads |
|---|---|---|
| Team Leader / Coordinator | _TBD_ | Roadmap, scope decisions, clinical-advisor outreach, integration |
| Business Analyst / Data Scientist | _TBD_ | KPIs, synthetic cohort, Trigger Discovery + Flare models, eval harness, business model |
| UI/UX / Frontend Developer | _TBD_ | PWA, Bangla UI/voice, verdict card, accessibility, Figma |
| Backend / Data Engineer | _TBD_ | APIs, Neo4j + pgvector, scrapers/parsers, agents, MCP servers, n8n, deployment |
| Presentation / Communication Lead | _TBD_ | Storyboard, video, 1-page summary, user interviews, portal documentation |
