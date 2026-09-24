# HappyGut Roadmap: from plan to finals

> Living document. Tick steps off as they finish. Dates are targets; **Oct 31 is fixed.**

## Planning and design steps

| Step | Window | Output | Status |
|---|---|---|---|
| **1. Strategy & scope** | Sep 24–27 | [`01-strategy.md`](01-strategy.md): stress test, positioning, hero flow, scope tiers, KPIs, rubric map | 🟡 Draft, awaiting team review |
| **2. Architecture & stack** | Sep 27–Oct 1 | `02-architecture.md`: agents, verdict engine, data model (SQL + graph), APIs, stack decision records, repo skeleton | ⏳ |
| **3. Data & knowledge design** | Sep 29–Oct 3 | [`03-data.md`](03-data.md): sources and licences, scrapers/parsers, Food KG schema, guideline corpus, synthetic cohort spec, data lifecycle, privacy | 🟡 In progress (§1–6 done) |
| **4. UX & Bangla design** | Sep 29–Oct 3 | `04-ux.md` + Figma: hero-flow screens, verdict card, check-in, Bangla copy, low-bandwidth rules | ⏳ |
| **5. Evaluation & safety plan** | Oct 1–4 | `05-evaluation.md`: test sets, metrics, red-flag suite, bias slices | ⏳ |

## Build steps

| Step | Window | Output |
|---|---|---|
| 6. Knowledge layer | Oct 1–8 | Food KG (~150 Bangladeshi dishes) in Neo4j · guideline corpus with contextual chunks in pgvector · ingestion scripts |
| 7. **Hero vertical slice** | Oct 4–14 | Photo/voice/text → verdict + why + citations in Bangla, end to end, deployed |
| 8. Personal intelligence | Oct 10–18 | Daily check-in · synthetic cohort · Trigger Discovery · Personal Gut Graph updates · Flare Early-Warning v0 |
| 9. Supporting features | Oct 15–22 | Generative Dietitian · clinician pre-visit PDF · MCP server #1 · n8n jobs |
| 10. Validate | Oct 12–26 | Eval report with real numbers · 5–10 patient interviews · 2–5 clinician interviews (Phase 3 "validation evidence") |
| 11. Package | Oct 24–30 | Public demo URL · 180s video · 1-page summary · portal fields filled from docs |
| **Submit** | **Oct 31** | Preliminary package |
| 12. Harden (if selected Nov 15) | Nov 15–Dec 20 | Wearables · FL simulation + DP · research dashboard · MCP #2–3 · offline mode · pilot · security review · rehearsal |
| **Finals** | **Dec 26** | 3-min live pitch + demo, Daffodil International University |

## Proposed role mapping (fill in names)

The team works across everything, but the portal needs named owners. This mapping gives each role the workstream it naturally leads.

| Official role | Name | Leads |
|---|---|---|
| Team Leader / Coordinator | _TBD_ | Roadmap, scope decisions, clinical-advisor outreach, integration |
| Business Analyst / Data Scientist | _TBD_ | KPIs, synthetic cohort, Trigger Discovery + Flare models, eval harness, business model |
| UI/UX / Frontend Developer | _TBD_ | PWA, Bangla UI/voice, verdict card, accessibility, Figma |
| Backend / Data Engineer | _TBD_ | APIs, Neo4j + pgvector, scrapers/parsers, agents, MCP servers, n8n, deployment |
| Presentation / Communication Lead | _TBD_ | Storyboard, video, 1-page summary, user interviews, portal documentation |
