# Tasks: Personal layer

**Input**: [spec.md](spec.md). Built on `claude/adoring-newton-9o7big` (2026-11-14/15).

## Engine (`engine/`, pure Python, unit-tested)
- [x] T001 `indices.py`: patient-reported HBI and SCCAI from diary answers; activity thresholds [US1]
- [x] T002 `sleep.py`: duration across midnight, late night relative to the person's median bedtime [US2]
- [x] T003 `periods.py`: remission / flare / settling from the daily index; rejected and manually marked flares [US4]
- [x] T004 `patterns.py`: Bayesian link per factor (food components at high level, sleep, stress, stressful periods, missed doses), worse days, minimum rate difference, overlap, everyday factors, per-period scope [US3]
- [x] T005 `flare_risk.py`: rule-based outlook v0 with named drivers [US3]
- [x] T006 `simulate.py`: simulated patients with injected patterns; tests recover them [FR-027]
- [x] T007 engine-v0.2: personal evidence strength rescaled around "no difference"; evidence applies at its learned level and one step below

## API (`services/api`)
- [x] T008 Diary: GET/PUT `/v1/diary/{date}` with pre-fill from meal checks, index, sleep facts, scrubbed notes, red-flag stop, 2-day edit window; `/v1/diary/days` [US1, US2]
- [x] T009 Stressful periods CRUD; days tagged [US2]
- [x] T010 Insights: patterns (all / remission / flare), periods + confirm / reject / manual, flare risk; learned food evidence and the confirmed flare state feed the meal verdict [US3, US4]
- [x] T011 Pre-visit report data [US5]
- [x] T012 Demo mode: one-tap login, simulated persona (120 days), labelled `is_synthetic`
- [ ] T013 Supabase migration and `PostgresStore` methods for diary, stressful periods and period decisions (these endpoints answer 501 on Postgres today)
- [ ] T014 Reminder and nudge delivery (web push / n8n) [US5]

## Web (`apps/web`)
- [x] T015 Nightly diary (5 steps, Bristol chart, per-food reactions, warning signs, result with score) [US1, US2]
- [x] T016 My patterns (scopes, counts, rate bars, overlap, explanation sheet) and flare-risk card [US3]
- [x] T017 My Gut (trend with flare shading, timeline, Remission / Flare tabs, week before each flare, proposals, manual flare, stressful periods) [US4]
- [x] T018 Doctor's report (printable) [US5]
- [x] T019 Bangla strings reviewed by the LLM judge (`data/review/llm_judge/bangla.md`)
- [x] T023 Personal Gut Graph view on My patterns
- [x] T024 Diary reminder notification while the app is open or installed (local notification; server push is T014)
- [x] T025 Health profile editing (diagnosis, stricture, lactose intolerance, IBS-like symptoms); a diagnosis change rescores the diary
- [x] T026 Food guide (every dish with the person's verdict) and Meal ideas (a week from dishes rated "likely OK"), computed by the engine
- [x] T027 Sample-data notice shown once at entry; per-screen labels removed (Constitution V, v2.0.0)
- [x] T028 Weight tracking (FR-029): weekly weigh-ins, trend and changes, GLIM-based notice, Today prompt, doctor's report; sample weigh-ins for the test accounts
- [x] T029 Medicines and tests (FR-030): own schedule, dose ticks, tests and appointments, on-device reminders, diary hint, doctor's report; sample schedules for the test accounts

## Proof (step 4)
- [ ] T020 Simulated cohort (≥ 200 patients × 180 days) and the recovery metrics SC-002 to SC-004 in the Eval Lab
- [ ] T021 Flare-risk v1 (LightGBM + SHAP on the cohort) against v0 (SC-005)
- [ ] T022 Timed diary walkthrough with 5 testers (SC-001)
