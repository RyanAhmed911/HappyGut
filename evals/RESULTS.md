# Evaluation results

Run on 2026-11-17 with `uv run python -m happygut_api.evaluate` (app 0.1.0, Pattern Finder `patterns-v0.1`). The run is deterministic: the same command gives the same numbers.

> **Read this first.** Every patient in section 1 is **simulated**. The simulator gives each one hidden contributors (for example "high-fat food raises symptoms"), and we measure whether the Pattern Finder recovers them. This shows the method works when a real effect exists; it is not evidence about real patients. No language model is involved in any number on this page.

## 1. Flare Pattern Finder on a simulated cohort

200 simulated patients, 120 days each, on a menu built from the 61 real dishes in the knowledge layer. Each patient has 0-5 hidden contributors (average 2.04): a food component (capsaicin_spice, fat, gos, lactose, red_processed_meat), late nights, high-stress days, exam periods, missed doses. 15% have none. About half also have a flare, which adds noise.

| Days of diary | Hidden contributors | Found | Recall | Companion reports | False reports | Precision | Precision counting companions as errors |
|---|---|---|---|---|---|---|---|
| 21 | 409 | 112 | 27% | 94 | 32 | 78% | 47% |
| 30 | 409 | 151 | 37% | 134 | 40 | 79% | 46% |
| 60 | 409 | 212 | 52% | 176 | 46 | 82% | 49% |
| 90 | 409 | 263 | 64% | 216 | 51 | 84% | 50% |
| 120 | 409 | 293 | 72% | 258 | 52 | 85% | 49% |

- **Found:** the app labels the factor "likely contributor" and it is one of that patient's hidden contributors.
- **Companion report:** the app labels a habit that comes together with a true one. In the simulator, as in life, an exam period brings high stress, late nights and missed doses; a late night means short, poor sleep; a flare brings poor sleep. Those habits really are followed by more bad days, so "linked" is a fair description (the app never says "caused" and adds an "often happens together with" note), but the app cannot tell which one is the driver.
- **False report:** labelled "likely contributor" with no hidden effect behind it and no companion.
- **Food only** (foods are independent of the habits, so this is the cleanest check): at 120 days 139 of 173 hidden food contributors were found, with 32 false food reports across 31 of 200 patients. Each patient is tested on 13 food components, so some false reports are expected; lowering them is the next piece of work on the method.
- Patients with no hidden contributor who still got a report at 120 days: 11 of 37.

Recall by kind of factor at 120 days:

| Kind | Found | Of | Recall |
|---|---|---|---|
| Food component | 139 | 173 | 80% |
| Late nights | 49 | 72 | 68% |
| High-stress days | 56 | 65 | 86% |
| Exam periods | 47 | 61 | 77% |
| Missed doses | 2 | 38 | 5% |

## 2. Red-flag sentinel

29 emergency phrases and 30 ordinary messages (`evals/sets/redflag.json`). The phrases were written by the team, so this is a development suite, not an independent test.

| Language | Emergency phrases caught | Ordinary messages wrongly flagged |
|---|---|---|
| English | 15 of 15 | 0 of 14 |
| Bangla | 9 of 9 | 0 of 10 |
| Bangla in English letters | 5 of 5 | 0 of 6 |

Two phrases added on 2026-11-17 ("I haven't passed urine all day and feel very dizzy" and a Bangla sentence with a word between "stomach" and "pain") were missed on the first run. The detector was extended, and both are now permanent tests.

## 3. Verdict engine on the real dishes

61 dishes × 7 patient profiles = 427 verdicts, with no personal history.

| Profile | Likely OK | Caution | Likely trigger | Not sure |
|---|---|---|---|---|
| Crohn's, remission | 61 | 0 | 0 | 0 |
| Crohn's, flare | 33 | 2 | 26 | 0 |
| Crohn's with a stricture | 27 | 13 | 21 | 0 |
| Crohn's, remission, lactose intolerant | 51 | 6 | 4 | 0 |
| Crohn's, remission, IBS-like symptoms | 56 | 0 | 5 | 0 |
| Ulcerative colitis, remission | 61 | 0 | 0 | 0 |
| Ulcerative colitis, flare | 33 | 2 | 26 | 0 |

In remission with nothing else in the profile, no dish gets a warning from the guidelines alone: the stronger rules belong to a stricture, lactose intolerance, IBS-like symptoms or a flare. For a person in remission the warnings come from their own diary (the Pattern Finder), which is the point of the personal layer.

- **Same answer every time:** 427 of 427 verdicts were identical when computed twice.
- **Every warning has a rule behind it:** 0 "caution" or "likely trigger" verdicts had no cited Rule Card.
- **Stricture rule:** 11 of 11 dishes with medium or high insoluble fibre, skins, seeds or nuts are rated "likely trigger" for a person with a stricture.
- **Speed:** the engine rates a three-dish meal in 0.21 ms (median; 90% under 0.25 ms, 300 runs). This is the engine alone, not the full check with a photo and a written explanation.

## 4. Dish names

Each stored name is looked up and must return its own dish (this checks the index for clashes; it is not a test on unseen spellings).

| Kind of name | Names | Lead to their own dish |
|---|---|---|
| Bangla | 61 | 61 |
| English | 61 | 61 |
| Other spellings (English letters and Bangla variants) | 209 | 209 |

## 5. Knowledge layer

61 dishes and 25 Rule Cards, all reviewed by an LLM judge against published sources (not by clinicians). 25 of 25 Rule Cards carry at least one exact sentence retrieved from a paper confirmed by DOI or PMID.

## Not measured yet

- Photo recognition accuracy on Bangladeshi meal photos (needs a labelled photo set).
- Agreement of verdicts with a dietitian-labelled food list.
- Full check time on a phone connection, including the photo and the written explanation.
- Anything on real patients.
