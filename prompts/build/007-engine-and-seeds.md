# P-007: Verdict engine and knowledge seeds
- **Category:** Implementation
- **Tool:** Claude Code
- **Date:** 2026-10-21

## Prompt
> Yes start
>
> *(in reply to: "Several Step 1–2 pieces don't need any keys, so I can start them while you set up accounts. Write the ~50 Bangladeshi dish entries and ~25 cited Rule Cards as drafts for your team to review, and build the verdict engine with unit tests for every rule.")*

## Output
- `engine/`: deterministic verdict engine, red-flag sentinel (EN/BN/Banglish), Bayesian Trigger Discovery; 62 tests
- `data/seeds/`: 61 Bangladeshi dish drafts and 25 Rule Card drafts. Written without internet access to the sources, so quotes are empty and every file is `status: draft` until human review (`docs/seed-review.md`)
- `pipelines/`: seed loader and validator (vocabulary, alias collisions, alternatives, approval rules), engine sanity tests on the real seeds; 9 tests
- `.github/workflows/tests.yml`: CI for both suites
