---
name: run-evals
description: Run the HappyGut evaluation suites (verdict set, red-flag suite, guideline RAG, Banglish dish names) and compare against the last run. Use before merging any change to prompts, models, retrieval, Rule Cards or the verdict engine.
---

# Run evals

1. Run the suites from `evals/` (commands are listed in `evals/README.md` once the harness exists):
   - `verdict`: accuracy, macro-F1, 🔴 recall on the labelled food set
   - `redflag`: recall must be **100%**
   - `rag`: Recall@5, MRR, Ragas faithfulness
   - `names`: Banglish/Bangla dish resolution Recall@1
2. Compare with the previous run (Parquet in `evals/results/`).
3. Gate: fail if red-flag recall < 100% or verdict accuracy drops by more than 2 points.
4. Report a short table of before/after numbers, and list any new failures so they can become test cases or few-shot examples.
5. Results on the simulated cohort are always reported as "simulated".
