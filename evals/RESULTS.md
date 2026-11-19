# Evaluation results

Run on 2026-11-19 with `uv run python -m happygut_api.evaluate` (app 0.1.0, Pattern Finder `patterns-v0.1`). The run is deterministic: the same command gives the same numbers.

> **Read this first.** Every patient in section 1 is **simulated**. The simulator gives each one hidden contributors (for example "high-fat food raises symptoms"), and we measure whether the Pattern Finder recovers them. This shows the method works when a real effect exists; it is not evidence about real patients. No language model is involved in any number on this page.

## 1. Flare Pattern Finder on a simulated cohort

200 simulated patients, 120 days each, on a menu built from the 109 real dishes in the knowledge layer. Each patient has 0-5 hidden contributors (average 2): a food component (capsaicin_spice, fat, gos, lactose, red_processed_meat, skins_seeds_nuts), late nights, high-stress days, exam periods, missed doses. 15% have none. About half also have a flare, which adds noise.

| Days of diary | Hidden contributors | Found | Recall | Companion reports | False reports | Precision | Precision counting companions as errors |
|---|---|---|---|---|---|---|---|
| 21 | 400 | 116 | 29% | 104 | 21 | 85% | 48% |
| 30 | 400 | 145 | 36% | 141 | 38 | 79% | 45% |
| 60 | 400 | 188 | 47% | 163 | 61 | 76% | 46% |
| 90 | 400 | 227 | 57% | 191 | 65 | 78% | 47% |
| 120 | 400 | 274 | 68% | 243 | 71 | 79% | 47% |

- **Found:** the app labels the factor "likely contributor" and it is one of that patient's hidden contributors.
- **Companion report:** the app labels a habit that comes together with a true one. In the simulator, as in life, an exam period brings high stress, late nights and missed doses; a late night means short, poor sleep; a flare brings poor sleep. Those habits really are followed by more bad days, so "linked" is a fair description (the app never says "caused" and adds an "often happens together with" note), but the app cannot tell which one is the driver.
- **False report:** labelled "likely contributor" with no hidden effect behind it and no companion.
- **Food only** (foods are independent of the habits, so this is the cleanest check): at 120 days 121 of 173 hidden food contributors were found, with 50 false food reports across 41 of 200 patients. Each patient is tested on 13 food components, so some false reports are expected; lowering them is the next piece of work on the method.
- Patients with no hidden contributor who still got a report at 120 days: 12 of 37.

Recall by kind of factor at 120 days:

| Kind | Found | Of | Recall |
|---|---|---|---|
| Food component | 121 | 173 | 70% |
| Late nights | 57 | 74 | 77% |
| High-stress days | 52 | 60 | 87% |
| Exam periods | 42 | 54 | 78% |
| Missed doses | 2 | 39 | 5% |

## 2. Red-flag sentinel

29 emergency phrases and 30 ordinary messages (`evals/sets/redflag.json`). The phrases were written by the team, so this is a development suite, not an independent test.

| Language | Emergency phrases caught | Ordinary messages wrongly flagged |
|---|---|---|
| English | 15 of 15 | 0 of 14 |
| Bangla | 9 of 9 | 0 of 10 |
| Bangla in English letters | 5 of 5 | 0 of 6 |

Two phrases added on 2026-11-17 ("I haven't passed urine all day and feel very dizzy" and a Bangla sentence with a word between "stomach" and "pain") were missed on the first run. The detector was extended, and both are now permanent tests.

## 3. Verdict engine on the real dishes

109 dishes × 7 patient profiles = 763 verdicts, with no personal history.

| Profile | Likely OK | Caution | Likely trigger | Not sure |
|---|---|---|---|---|
| Crohn's, remission | 109 | 0 | 0 | 0 |
| Crohn's, flare | 59 | 6 | 44 | 0 |
| Crohn's with a stricture | 55 | 24 | 30 | 0 |
| Crohn's, remission, lactose intolerant | 92 | 10 | 7 | 0 |
| Crohn's, remission, IBS-like symptoms | 101 | 0 | 8 | 0 |
| Ulcerative colitis, remission | 109 | 0 | 0 | 0 |
| Ulcerative colitis, flare | 58 | 7 | 44 | 0 |

In remission with nothing else in the profile, no dish gets a warning from the guidelines alone: the stronger rules belong to a stricture, lactose intolerance, IBS-like symptoms or a flare. For a person in remission the warnings come from their own diary (the Pattern Finder), which is the point of the personal layer.

- **Same answer every time:** 763 of 763 verdicts were identical when computed twice.
- **Every warning has a rule behind it:** 0 "caution" or "likely trigger" verdicts had no cited Rule Card.
- **Stricture rule:** 19 of 19 dishes with medium or high insoluble fibre, skins, seeds or nuts are rated "likely trigger" for a person with a stricture.
- **Speed:** the engine rates a three-dish meal in 0.16 ms (median; 90% under 0.18 ms, 300 runs). This is the engine alone, not the full check with a photo and a written explanation.

## 4. Dish names

Each stored name is looked up and must return its own dish (this checks the index for clashes; it is not a test on unseen spellings).

| Kind of name | Names | Lead to their own dish |
|---|---|---|
| Bangla | 109 | 109 |
| English | 109 | 109 |
| Other spellings (English letters and Bangla variants) | 477 | 477 |

## 5. Knowledge layer

109 dishes and 25 Rule Cards, all reviewed by an LLM judge against published sources (not by clinicians). 25 of 25 Rule Cards carry at least one exact sentence retrieved from a paper confirmed by DOI or PMID.

## Not measured yet

- Photo recognition accuracy on Bangladeshi meal photos (needs a labelled photo set).
- Agreement of verdicts with a dietitian-labelled food list.
- Full check time on a phone connection, including the photo and the written explanation.
- Anything on real patients.
