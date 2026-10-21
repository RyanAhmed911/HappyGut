# HappyGut Roadmap: from plan to finals

> Living document. Tick steps off as they finish. Dates are targets; **Oct 31 is fixed.**

## Planning and design steps

| Step | Window | Output | Status |
|---|---|---|---|
| **1. Strategy & scope** | Sep 24–27 | [`01-strategy.md`](01-strategy.md): stress test, positioning, hero flow, scope tiers, KPIs, rubric map | 🟡 Draft, awaiting team review |
| **2. Architecture & stack** | Oct 21 | [`02-architecture.md`](02-architecture.md): system, hero-flow sequence, verdict engine, repo layout, decisions | ✅ v1.0 |
| **3. Data & knowledge design** | Sep 29–Oct 3 | [`03-data.md`](03-data.md): sources and licences, scrapers/parsers, Food KG schema, guideline corpus, synthetic cohort spec, data lifecycle, privacy | ✅ Drafted (§1–10) |
| **4. UX & Bangla design** | Sep 29–Oct 3 | `04-ux.md` + Figma: hero-flow screens, verdict card, check-in, Bangla copy, low-bandwidth rules | ⏳ |
| **5. Evaluation & safety plan** | Oct 1–4 | `05-evaluation.md`: test sets, metrics, red-flag suite, bias slices | ⏳ |

## Build plan (Oct 21 → Oct 30)
Scope = tiers A and B in [`portal/submission-scope.md`](portal/submission-scope.md). Architecture: [`02-architecture.md`](02-architecture.md). Rules: [`../.specify/memory/constitution.md`](../.specify/memory/constitution.md).

| Day | Step | Spec | Done means | Status |
|---|---|---|---|---|
| Oct 21 | **0. Foundation** | — | Accounts + GPU machine ready ([`setup.md`](setup.md)); skeleton, constitution, AGENTS.md, skills, specs 001–002 pushed | 🟡 Repo part done; accounts pending |
| Oct 22–23 | **1. Knowledge layer** | [001](../specs/001-knowledge-layer/spec.md) | ~50 dishes + ~25 Rule Cards in Neo4j; contextual hybrid RAG in pgvector; foodgraph MCP | ⏳ |
| Oct 23–25 | **2. Hero flow** | [002](../specs/002-meal-check/spec.md) | Photo/text → Bangla verdict card with citations, end to end on a phone | ⏳ |
| Oct 25–26 | **3. Personal layer** | 003 | Check-in, simulated cohort, Trigger Discovery, early-warning score, "My Gut" | ⏳ |
| Oct 26–27 | **4. Proof** | 004 | Eval sets, red-flag suite, RAG ablation, Eval Lab; remaining MCP servers; n8n | ⏳ |
| Oct 28 | **5. Ship** | — | Deployed URL, demo account, /docs, clinician PDF, Figma prototype | ⏳ |
| Oct 29 | **6. Video** | — | 180s video on YouTube + Facebook, 1-page summary | ⏳ |
| Oct 30 | **7. Reconcile & submit** | — | Checklist in `portal/submission-scope.md` §4 done; submitted a day early | ⏳ |

**Cut order if behind:** smolagents → CrewAI → DSPy → embedding fine-tune → research MCP → LightGBM → dietitian agent. Never cut: hero flow, evals, video.

## Proposed role mapping (fill in names)

The team works across everything, but the portal needs named owners. This mapping gives each role the workstream it naturally leads.

| Official role | Name | Leads |
|---|---|---|
| Team Leader / Coordinator | _TBD_ | Roadmap, scope decisions, clinical-advisor outreach, integration |
| Business Analyst / Data Scientist | _TBD_ | KPIs, synthetic cohort, Trigger Discovery + Flare models, eval harness, business model |
| UI/UX / Frontend Developer | _TBD_ | PWA, Bangla UI/voice, verdict card, accessibility, Figma |
| Backend / Data Engineer | _TBD_ | APIs, Neo4j + pgvector, scrapers/parsers, agents, MCP servers, n8n, deployment |
| Presentation / Communication Lead | _TBD_ | Storyboard, video, 1-page summary, user interviews, portal documentation |
