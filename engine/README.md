# engine: verdict engine, red-flag sentinel and Trigger Discovery

Pure Python, no network calls, every rule unit-tested. This package decides verdicts; LLMs never do (Constitution III).

| Module | What it does |
|---|---|
| `verdict.py` | Graded verdict per dish and meal: hard rules → guideline score (severity × level × state) → personal trigger / tolerance → confidence gate (⚪) → gentler alternative. Algorithm: `docs/02-architecture.md` §3 |
| `redflag.py` | Rule-based red-flag sentinel (English, Bangla, Banglish): heavy bleeding, fever with abdominal pain, possible obstruction, severe dehydration. Tuned for recall |
| `triggers.py` | Personal Trigger Discovery: 6–48 h exposure windows, Beta posteriors, P(exposed rate > baseline), 90% credible intervals |
| `config.py` | All weights and thresholds (versioned) |
| `vocab.py` | Component vocabulary, levels, verdicts, diagnoses, states |

```bash
cd engine && uv run --group dev pytest -q
```
