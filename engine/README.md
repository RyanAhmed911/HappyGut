# engine: verdict engine, red-flag sentinel and Trigger Discovery

Pure Python, no network calls, every rule unit-tested. This package decides verdicts; LLMs never do (Constitution III).

| Module | What it does |
|---|---|
| `verdict.py` | Graded verdict per dish and meal: hard rules → guideline score (severity × level × state) → personal trigger / tolerance → confidence gate (⚪) → gentler alternative. Algorithm: `docs/02-architecture.md` §3 |
| `redflag.py` | Rule-based red-flag sentinel (Bangla, English, plus romanised-Bangla phrases as a safety net): heavy bleeding, fever with abdominal pain, possible obstruction, severe dehydration. Tuned for recall |
| `triggers.py` | Personal Trigger Discovery: 6–48 h exposure windows, Beta posteriors, P(exposed rate > baseline), 90% credible intervals |
| `indices.py` | Patient-reported HBI (Crohn's) and SCCAI (UC) from the nightly diary answers, with the activity thresholds |
| `sleep.py` | Sleep duration across midnight; "late night" relative to the person's own usual bedtime |
| `periods.py` | Remission / flare / settling periods from the daily index (flare: active 3 of 4 days; ends after 7 calm days); the user's decisions win |
| `patterns.py` | Flare Pattern Finder: Bayesian link between each factor (food components, late / short / poor sleep, high stress, stressful periods, missed doses) and worse days; overlap between factors; food results feed the verdict |
| `flare_risk.py` | Flare-risk outlook v0: transparent points from index trend, the person's own contributors, upcoming stressful periods and missed doses |
| `simulate.py` | Simulated patients with injected patterns, to measure how well the Pattern Finder recovers them (always labelled simulated) |
| `config.py` | All weights and thresholds (versioned) |
| `vocab.py` | Component vocabulary, levels, verdicts, diagnoses, states |

```bash
cd engine && uv run --group dev pytest -q
```
