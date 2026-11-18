# Flare-risk model v1 (LightGBM)

Trained 2026-11-18 with `uv run python -m happygut_api.flare_model train` (deterministic). Model card: `services/api/src/happygut_api/models/flare-risk-v1.json`.

> **Read this first.** The model learned from **simulated** patients and is tested on other simulated patients. It shows the method works when the effects exist in the data; it says nothing yet about real patients. In the app it is an estimate shown next to the rule-based outlook, never a diagnosis and never a reason to change a medicine.

**Question:** Does a flare start within the next 3 days? (asked on days not already in a flare)

**Data:** 200 simulated patients × 120 days. Patients are split, never days: 100 train, 50 pick the number of trees, 50 are held out. The first 14 days of each patient are skipped. Held-out: 4862 days, 98 of them with a flare starting within 3 days (2.0%). Flare history is used only as it was known on each day.

## v1 against the rule-based v0, on the held-out patients

| | ROC AUC | Average precision | Flagging the top 10% of days: flare starts caught | Top 20%: caught |
|---|---|---|---|---|
| **v1 (LightGBM)** | **0.658** | **0.077** | 30 of 98 (31%) | 41 of 98 (42%) |
| v0 (rules) | 0.558 | 0.031 | 11 of 98 (11%) | 21 of 98 (21%) |
| Chance | 0.5 | 0.020 | 10% | 20% |

Spec 003 SC-005 (v1 beats v0 on ROC AUC): **met**. v1 Brier score 0.0193 (lower is better; always guessing the base rate scores 0.0198).

## What the model relies on most

| Feature | Gain |
|---|---|
| days_since_flare | 3164.9 |
| stressful_period_soon | 1616.3 |
| index_rise | 1151.8 |
| index_mean_3 | 670.4 |
| stress_mean_3 | 588.9 |
| index_max_7 | 547.2 |
| index_today | 445.2 |
| flare_days_30 | 371.2 |
| in_stressful_period | 349.8 |
| active_days_7 | 342.7 |

In the app each estimate shows its own top three drivers: exact SHAP values from LightGBM's TreeSHAP.

## Limits

- Simulated patients only; the simulator's flares start at random times, so part of every flare can't be predicted by any model.
- The cohort uses the Harvey-Bradshaw Index (Crohn's). For ulcerative colitis (SCCAI) the app still shows the estimate, but the model has not been checked on that scale.
- Not used on days already in a flare: the question is about new flares.
