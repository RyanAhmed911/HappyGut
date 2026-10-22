# HappyGut: instructions for coding agents

This file is the shared memory for every coding agent on this repo (Claude Code, Cursor, Lovable, Codex and others). `CLAUDE.md` imports it.

HappyGut is an AI-native chronic-care companion for people with Inflammatory Bowel Disease (Crohn's disease, ulcerative colitis), built for the International AI Builders Congress 2026 (HealthSphere AI · ChronicCare AI). Preliminary deadline: **2026-10-31**. Finals: **2026-12-26**.

## Read first
- `.specify/memory/constitution.md`: the rules (they override everything else)
- `docs/02-architecture.md`: system, verdict engine, repo layout, decisions
- `docs/portal/submission-scope.md`: what is tier A / B / C for the Oct 31 prototype
- `docs/00-roadmap.md`: current step

## Hero flow (protect this above everything else)
Snap a Bangladeshi dish or label, or type Bangla/English/Banglish → **personal verdict** (🟢 Likely OK for you / 🟡 Caution / 🔴 Likely trigger for you / ⚪ Not sure) with *why*, citations and an alternative → log meal → Personal Gut Graph updates.

## Non-negotiable product rules
1. Never label a food "safe". Use the graded verdicts above.
2. The LLM does perception and explanation; the **verdict is computed by the deterministic, unit-tested engine** in `engine/`.
3. Every health claim cites retrieved evidence. No evidence → ⚪ "Not sure".
4. Stricturing Crohn's rules (avoid insoluble fibre, skins, seeds, nuts) apply before any LLM output.
5. Red-flag symptoms (heavy bleeding, fever + abdominal pain, signs of obstruction, severe dehydration) → stop diet advice and escalate to a clinician or emergency care.
6. Never suggest starting, stopping or changing medication.
7. Scrub PII inside our backend (Presidio + Bangladesh rules + Bengali NER) before any cloud LLM call. Treat the project as having no local GPU: nothing live or day-to-day may depend on it (it's only for occasional one-off batch sessions). Never commit real patient data or secrets. Synthetic data is flagged `is_synthetic` and labelled "simulated".
8. Only legally licensed data sources; record each licence in `docs/03-data.md` before ingesting.
9. Every user-facing string exists in Bangla and English (i18n files).
10. Free tiers with no card only. No Google Cloud / Vertex, AWS or paid domains.

## Conventions
- Python 3.11, FastAPI, Pydantic v2, pytest. TypeScript strict, React + Vite, Zod.
- Long prompts live in `prompts/runtime/` as versioned files; don't inline them in code.
- Knowledge seeds: dishes in `data/seeds/dishes/*.yaml`, Rule Cards in `data/seeds/rule_cards/*.yaml` (formats in `.claude/skills/add-dish` and `.claude/skills/add-rule-card`).
- Spec-Kit per feature: specs in `specs/NNN-name/`.
- One PR per task, reviewed by a human. Record decisions in the relevant `docs/` decision log.
