# HappyGut: project context for AI coding agents

HappyGut is an AI-native chronic-care companion for people with Inflammatory Bowel Disease (Crohn's disease, ulcerative colitis). It's being built for the International AI Builders Congress 2026 (Domain: HealthSphere AI · Challenge: ChronicCare AI). Preliminary deadline: **2026-10-31**. Finals: **2026-12-26**.

## Read first
- `docs/00-roadmap.md`: current step and timeline
- `docs/01-strategy.md`: scope, hero flow, decision log (D1–D9)

## Hero flow (protect this above everything else)
Snap a Bangladeshi dish / label, or speak Bangla/English/Banglish → **personal verdict** (🟢 Likely OK for you / 🟡 Caution / 🔴 Likely trigger for you / ⚪ Not sure) with *why*, citations and an alternative → log meal → Personal Gut Graph updates.

## Non-negotiable product rules
1. Never label a food "safe". Use the graded verdicts above.
2. The LLM does perception and explanation; the **verdict is computed by a transparent, unit-tested scoring function** over knowledge-graph, guideline and personal evidence.
3. Every health claim must cite retrieved evidence (guideline, composition data, or the user's own history). If there's no evidence, return ⚪ "Not sure".
4. Stricturing Crohn's rules (avoid insoluble fibre, skins, seeds, nuts) apply before any LLM output.
5. Red-flag symptoms (heavy bleeding, fever + abdominal pain, signs of obstruction, severe dehydration) → stop diet advice and escalate to a clinician or emergency care.
6. Never suggest starting, stopping or changing medication. Adherence reminders and logging only.
7. Strip PII with the local model before any cloud LLM call. Never commit real patient data. Test data is synthetic and must be labelled as synthetic.
8. Only use legally licensed data sources, and record the licence of each one in `docs/03-data.md`.
9. Every user-facing string must exist in both Bangla and English.

## Repo conventions
- Prompts live in `prompts/` as versioned markdown files (the competition's prompt library). Don't inline long prompts in code.
- Record architecture decisions in the relevant `docs/` file's decision log.
