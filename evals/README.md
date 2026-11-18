# evals: evaluation

```bash
cd services/api
uv run python -m happygut_api.evaluate            # full run, about 6 minutes on 4 cores
uv run python -m happygut_api.evaluate --patients 40
```

Writes [`RESULTS.md`](RESULTS.md) (the report), `summary.json`, and `apps/web/src/data/evaluation.json` (the few numbers the app's "How it works" page shows; a test checks it matches). The run is deterministic and calls no language model.

| Suite | What it measures | Gate in CI |
|---|---|---|
| Simulated cohort | Whether the Flare Pattern Finder recovers hidden contributors, at 21 to 120 days of diary | Scoring is reproducible |
| Red flags (`sets/redflag.json`) | Emergency phrases caught and ordinary messages wrongly flagged, by language | Every phrase caught, no false alarm |
| Verdict rules | Reproducibility, a rule behind every warning, the stricture rule, on the real dishes | All three hold |
| Dish names | Every stored name leads back to its own dish | All names resolve |

The flare-risk model v1 has its own run and report: `uv run python -m happygut_api.flare_model train` writes the model, its card and [`FLARE_MODEL.md`](FLARE_MODEL.md) (about 10 minutes on 4 cores; a test checks the shipped model still beats the rules).

Results on the simulated cohort are always reported as "simulated". Not built yet: verdict agreement with a dietitian-labelled list, photo recognition accuracy, guideline retrieval (Ragas), the Streamlit Eval Lab.
