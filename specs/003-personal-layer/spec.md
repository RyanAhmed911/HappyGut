# Feature Specification: Personal layer (nightly diary, sleep, stress, Flare Pattern Finder, remission and flare periods)

**Feature Branch**: `003-personal-layer`

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "Personal layer: nightly food & symptom diary, sleep and stress tracking, Flare Pattern Finder, and separate remission / flare periods. (1) Every night before sleep the app asks what the user ate across the whole day (meals already checked are pre-filled), whether each food caused stomach ache, bloating or urgency, plus stool changes and small notes; this replaces the separate daily check-in and still produces the HBI or SCCAI score. (2) Sleep: bedtime, wake time, sleep quality; does late or short sleep make symptoms worse for this user? (3) Stress: daily stress level plus tagged stressful periods such as exams; does stress make symptoms worse? (4) Flare Pattern Finder: learn from daily data which of this user's habits most likely contribute to symptom worsening and flares (personal Bayesian model + a gradient-boosted model with explanations trained on a simulated cohort); shown as likely contributors, never proven causes, never medication advice. (5) Remission and flare periods detected from the daily clinical index and the user's confirmation, shown separately. Bangla and English only. Red-flag answers stop the flow and escalate. Simulated data is labelled simulated."

## Context

This feature is the "personal" half of the Personal Gut Graph. Feature 002 (meal check) answers "is this meal likely to trigger me?" at the moment of eating. This feature closes the loop: every night it collects what actually happened that day, and over weeks it learns which foods **and habits** (late nights, short sleep, stress, exam periods, missed doses) are followed by worse symptoms for this one person. It also separates the user's history into remission and flare periods, because what a gut tolerates in remission often differs from what it tolerates in a flare.

The results feed back into feature 002: learned food-component triggers become personal evidence in the verdict engine, and the current period (remission or flare) sets the disease state the verdict uses.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Nightly food and symptom diary (Priority: P1)

At a bedtime the user picks (default 22:30), the app sends a reminder: "How was your gut today?" The diary takes about 2 minutes:

1. **Food today.** Meals already checked during the day are listed. The user adds anything missing (by typing in Bangla or English, picking from recent foods, or snapping a photo) and roughly when they ate it (morning, noon, afternoon, evening, night).
2. **Did any food bother you?** For each food, the user can tap "stomach ache", "bloating", "urgency / ran to the toilet", "nausea" or "fine". This is optional per food.
3. **Stool today.** Number of stools, the most typical form (Bristol stool chart pictures 1–7), any blood (none / streaks / a lot), mucus, urgency, and whether they woke at night to go.
4. **How do you feel.** Abdominal pain (none / mild / moderate / severe) and general well-being (very well … terrible).
5. **Medication.** Whether they took today's doses (taken / missed / not applicable). This is logging only.
6. **Notes.** A free-text box for small details ("ate at a wedding", "period started", "travelled").

When the user saves, the app shows today's clinical index (HBI for Crohn's, SCCAI for UC) and a one-line comparison with their recent days.

**Why this priority**: Every other part of this feature learns from these daily records. Without the diary there is nothing to analyse. It replaces the separate daily check-in planned earlier, so the user answers one short questionnaire a day instead of two.

**Independent Test**: With a test persona, complete diaries for 3 days, including one day with an added meal and one food marked "stomach ache". Check that each day is stored with its foods, reactions, stool details, index score and timestamps, and that meals checked earlier through feature 002 were pre-filled and not duplicated.

**Acceptance Scenarios**:

1. **Given** the user checked two meals today through the meal check, **When** they open tonight's diary, **Then** both meals are already listed and the user only adds the missing ones.
2. **Given** the user enters stool and pain answers, **When** they save, **Then** the app calculates and shows the matching HBI or SCCAI score for their diagnosis.
3. **Given** the user marks "a lot" of blood, or fever with abdominal pain, or vomiting with no stool or gas, or signs of severe dehydration, **When** they continue, **Then** the diary stops, no diet or lifestyle feedback is shown, and the escalation screen tells them to contact their doctor or emergency care. What they entered so far is still saved.
4. **Given** the user ignores the reminder, **When** they open the app the next morning, **Then** they can still fill in yesterday's diary (up to 2 days back), and the entry is marked as filled in late.
5. **Given** the user's language is Bangla, **Then** every question, answer option, reminder and result is in Bangla.

---

### User Story 2 - Sleep and stress tracking (Priority: P1)

The diary also asks three quick questions:
- **Sleep last night:** bedtime, wake-up time and quality (good / OK / poor). The app works out sleep duration and whether the night was "late" compared with the user's usual bedtime.
- **Stress today:** a 0–4 scale (none … very high).
- **Stressful period:** the user can mark a period in advance or afterwards, such as "Exams 10–24 Nov", "Ramadan", "work deadline" or "family event". Days inside the period are tagged automatically.

**Why this priority**: The user specifically wants to know whether going to sleep late and stress (for example before exams) make their symptoms worse. Sleep and stress also confound food triggers: a bad week of exams can make an innocent food look guilty. Recording them makes the food analysis more honest.

**Independent Test**: Enter a 14-day history containing 4 late nights and a 5-day exam period. Check that each day carries its sleep duration, "late night" flag, stress score and period tag.

**Acceptance Scenarios**:

1. **Given** the user went to bed at 02:30 while their usual bedtime is 23:30, **When** the diary is saved, **Then** that night is flagged "late" and its duration is calculated correctly across midnight.
2. **Given** the user created a period "Exams 10–24 Nov", **Then** every diary day from 10 to 24 November is tagged "exam", including days filled in afterwards.
3. **Given** the user skips the sleep or stress questions, **Then** the diary still saves, and those days are left out of the sleep or stress analysis instead of being counted as "normal".

---

### User Story 3 - Flare Pattern Finder: "what might be making me worse?" (Priority: P1)

A "My patterns" screen answers: *"What am I doing that is followed by my symptoms getting worse?"* It lists the user's likely contributors, strongest first, for example:

- 🔴 **Late nights (after 1 am)**: "On 5 of the 7 days after a late night your symptoms were worse, compared with 4 of 20 other days." Likely contributor.
- 🟡 **Exam weeks**: "Your average score was 6.1 during exams and 3.2 outside them." Possible contributor; more data needed.
- 🔴 **High-fat meals**: "4 of your last 5 high-fat meals were followed by symptoms within 48 hours." Likely contributor.
- ⚪ **Lactose**: "Not enough data yet (2 exposures)."
- 🟢 **Spicy food**: "Not linked to your symptoms so far (9 exposures)."

Each item shows how many times it happened, what happened afterwards, the uncertainty in plain words ("fairly sure" / "not sure yet"), and the time window used. A short footer says that these are patterns in the user's own data, not proven causes, and that the user should discuss them with their doctor.

The screen also shows a **flare-risk outlook** for the next few days ("Your risk of a flare is higher than usual this week"), with the top three factors driving it.

**Why this priority**: This is the feature the user described as "figure out what this person is doing that caused the flare". It is the core of the personalisation story and the main "AI that learns from you" moment in the demo.

**Independent Test**: Run the Pattern Finder on the simulated demo persona, whose 90-day history has injected effects (late nights worsen symptoms; high fat is a trigger; spice is not). Check that late nights and high fat are listed as likely contributors and spice is not. Then run it across the simulated cohort and report precision and recall of the injected patterns.

**Acceptance Scenarios**:

1. **Given** a factor with fewer than 3 exposures, **Then** it is shown as ⚪ "Not enough data yet", never as a contributor.
2. **Given** late nights are followed by worse symptoms much more often than other nights, with at least 3 late nights logged, **Then** "Late nights" appears as a likely contributor with its counts.
3. **Given** a factor that is often present on bad days but only because it happens during exam weeks (e.g. instant noodles eaten only during exams), **Then** the screen notes that the two overlap ("mostly happened during exams") instead of presenting both as independent causes.
4. **Given** any result, **Then** the wording never says a factor "caused" a flare, never calls any food or habit "safe", and never suggests starting, stopping or changing medication. Missed doses may be listed as a pattern, with the advice to talk to the doctor.
5. **Given** the persona is simulated, **Then** the screen carries a "simulated data" label.

---

### User Story 4 - Remission and flare periods shown separately (Priority: P1)

A "My Gut" timeline colours each day by period: **remission**, **flare**, or **settling** (in between). Periods come from the daily clinical index and are confirmed by the user ("It looks like a flare started on 3 Nov. Is that right?"). The user can also mark a period themselves, for example when their doctor confirmed a flare.

Below the timeline, the user can switch between **Remission** and **Flare** tabs. Each tab shows, for that kind of period only:
- how many days and how many separate periods, and the average and worst index score
- average stools per day, days with blood, average pain and sleep
- foods and habits that were followed by worse symptoms in this kind of period, and the ones that were not
- for flares: what was going on in the 7 days before each flare started (late nights, stress, exam periods, missed doses, risky foods)

**Why this priority**: The user wants remission and flare periods kept apart. It is also clinically meaningful: the verdict engine already treats flare and remission differently, and a food that is fine in remission may not be fine in a flare.

**Independent Test**: Load a 120-day simulated history with two flares. Check that both flares are detected within 3 days of their injected start dates, that the timeline shows them, and that the Remission and Flare tabs each show statistics computed only from their own days.

**Acceptance Scenarios**:

1. **Given** the index is at or above the "active" threshold on at least 3 of 4 consecutive days, **Then** the app proposes a flare starting on the first of those days and asks the user to confirm.
2. **Given** a flare, **When** the index stays below the "remission" threshold for 7 consecutive days, **Then** the app proposes that the flare has ended and the user is back in remission.
3. **Given** the user confirms a flare, **Then** the meal check (feature 002) uses "flare" as the current state until the flare ends.
4. **Given** the user rejects a proposed period, **Then** the user's answer wins and is kept; the app doesn't propose the same period again.
5. **Given** fewer than 7 days of diaries, **Then** the timeline shows the days logged but no periods yet, with the message "Keep logging for a week to see your periods".

---

### User Story 5 - Gentle nudges and the doctor's view (Priority: P2)

When the flare-risk outlook rises, or a known personal contributor is coming up (for example an exam period the user has marked), the app sends one gentle nudge a day at most: "Exams start Monday. Your symptoms have tended to get worse in exam weeks. Gentler meals and regular sleep may help; talk to your doctor if symptoms rise." The pre-visit report for the doctor includes the period timeline, the likely contributors and the remission vs flare summaries.

**Why this priority**: This completes the ChronicCare loop (data → alerts → coaching), but the story still works without it.

**Independent Test**: With an exam period marked 3 days ahead and "exam weeks" as a contributor, check that exactly one nudge is generated, in the user's language, with no medication advice.

**Acceptance Scenarios**:

1. **Given** a nudge was sent today, **Then** no second nudge is sent the same day.
2. **Given** the user turns nudges off, **Then** none are sent; the diary reminder is a separate setting.

---

### Edge Cases

- **Diary filled in late or missed.** A diary can be completed up to 2 days later. Missing days are gaps, never "symptom-free" days.
- **Unknown food.** A food the knowledge graph can't resolve is still logged as free text. It counts towards "foods that bothered you" but has no components, so it adds nothing to the component analysis until resolved.
- **Overlapping factors.** Late nights during exam weeks, or wedding food on a late night, are reported as overlapping rather than double-counted (User Story 3, scenario 3).
- **Delayed effects.** Food effects are looked for 6–48 hours later, sleep effects on the next 1–2 days, stress and exam effects on the same day up to 3 days later. These windows are configurable and shown on screen.
- **Women's cycle.** The user may tag menstruation days in notes or as a period type; tagged days are treated as a possible confounder.
- **Red flags in free text.** Notes are checked by the same red-flag sentinel as the meal check (feature 002); a red-flag phrase stops the flow.
- **Very irregular sleepers (shift work).** "Late" is defined relative to the user's own median bedtime, not a fixed clock time; short sleep is defined by duration.
- **Changing diagnosis or phenotype.** If the user changes their diagnosis, past index scores stay as calculated; new days use the new index.
- **Diary text in a language other than Bangla or English.** The text is stored as free text; nothing is guessed from it.

## Requirements *(mandatory)*

### Functional Requirements

**Nightly diary**
- **FR-001**: The system MUST send one diary reminder per day at a time the user chooses (default 22:30 local time), and let the user turn it off.
- **FR-002**: The diary MUST pre-fill every meal checked that day through feature 002, and let the user add, edit or remove foods, each with an approximate time of day.
- **FR-003**: For each food the user MUST be able to record no reaction, or any of: stomach ache, bloating, urgency, nausea.
- **FR-004**: The diary MUST record number of stools, the typical Bristol stool type (1–7, chosen from pictures), blood (none / streaks / a lot), mucus, urgency, night-time stools, abdominal pain, general well-being, medication taken (taken / missed / not applicable) and optional free-text notes.
- **FR-005**: The system MUST calculate the patient-reported HBI (Crohn's) or SCCAI (UC) from the diary answers and store it with the day.
- **FR-006**: Red-flag answers or phrases (a lot of blood, fever with abdominal pain, vomiting with no stool or gas, signs of severe dehydration) MUST stop the diary, suppress all diet and lifestyle feedback, show the escalation screen, and save what was entered.
- **FR-007**: A diary MUST be completable up to 2 days after its date and is marked as completed late; days without a diary MUST be treated as missing, not as symptom-free.
- **FR-008**: The diary MUST take a median of under 2 minutes for a returning user.

**Sleep and stress**
- **FR-009**: The diary MUST record bedtime, wake-up time and sleep quality for the previous night, and derive sleep duration (correct across midnight) and a "late night" flag relative to the user's own median bedtime over the last 14 days (default: more than 90 minutes later). Until 7 nights are logged, a fixed default of 01:00 applies.
- **FR-010**: The diary MUST record a daily stress level (0–4).
- **FR-011**: The user MUST be able to create, edit and delete named stressful periods (types: exam, work, family, religious fasting, travel, menstruation, other) with start and end dates, before or after they happen; all diary days in the range are tagged.
- **FR-012**: Skipped sleep or stress answers MUST be stored as missing and left out of the analyses that need them.

**Flare Pattern Finder**
- **FR-013**: The system MUST analyse, per user, these candidate factors: each food component (the vocabulary used by the verdict engine), late night, short sleep (< 6 h), poor sleep quality, high stress (≥ 3), each stressful-period type, missed medication doses, and foods the user marked as bothering them.
- **FR-014**: For each factor the system MUST compare how often a "worse day" follows days with the factor and days without it, within the factor's time window, and give: number of exposures, number followed by a worse day, the comparison rate, the probability that the factor is linked to worse days, and an uncertainty range. A "worse day" is a day whose index is at least 2 points above the user's own 14-day median, or a diary day with a food reaction marked.
- **FR-015**: A factor MUST be labelled a likely contributor only with at least 3 exposures and a link probability above 0.8. Factors with fewer than 3 exposures MUST show "Not enough data yet". Factors with enough exposures and a link probability below 0.5 are shown as "not linked so far".
- **FR-016**: When two factors occur together on most of the same days (more than 70% overlap), the system MUST report the overlap instead of listing them as independent contributors.
- **FR-017**: The system MUST produce a flare-risk outlook for the next 3 days. Version 0 is a transparent, rule-based score from the index trend, the user's likely contributors present in the last 3 days, upcoming marked stressful periods, and missed doses. Version 1 adds a gradient-boosted model trained only on the simulated cohort, with per-factor contributions (SHAP values) shown as the top three drivers. Both show the factors behind the score.
- **FR-018**: All pattern and outlook results MUST be computed by deterministic, unit-tested code (or a versioned, evaluated trained model for the v1 outlook), not by an LLM. An LLM may only turn the computed results into plain-language sentences, and those sentences MUST match the computed numbers (output guard).
- **FR-019**: Pattern wording MUST say "linked to", "followed by" or "likely contributor", never "caused", never call a food or habit "safe", and never suggest starting, stopping or changing medication.
- **FR-020**: Learned food-component results MUST be written back as personal evidence for the meal check (feature 002), and only these (not sleep or stress factors) affect meal verdicts.

**Remission and flare periods**
- **FR-021**: The system MUST propose period changes from the daily index: a flare when the index is at or above the active threshold on at least 3 of 4 consecutive days; remission after 7 consecutive days below the remission threshold; "settling" otherwise. Thresholds: HBI active ≥ 5, remission < 5; SCCAI active ≥ 5, remission ≤ 2. All thresholds and windows are configurable and versioned.
- **FR-022**: Every proposed period change MUST be confirmed or rejected by the user. The user's answer always wins, and the user can also mark periods manually.
- **FR-023**: The confirmed current period MUST set the disease state used by the meal check (flare or remission).
- **FR-024**: The system MUST show a timeline of periods and separate Remission and Flare summaries: number of days and periods, average and worst index, average stools per day, days with blood, average pain, average sleep duration, the Pattern Finder results computed only within that kind of period (shown once each kind has at least 14 days), and, for flares, the factors present in the 7 days before each flare started.

**Cross-cutting**
- **FR-025**: Every user-facing string, reminder and result MUST exist in Bangla and English. Free-text input is accepted in Bangla or English; Banglish (romanised Bangla sentences) is not a supported input language.
- **FR-026**: Free-text notes MUST be scrubbed of personal identifiers inside the backend before any cloud AI call, the same as the meal check.
- **FR-027**: A simulated cohort (at least 200 patients × 180 days) and a simulated demo persona MUST be generated with known, injected effects for food components, late nights, stress and exam periods, plus confounders and missing days. They MUST be flagged `is_synthetic` and labelled "simulated" wherever shown.
- **FR-028**: Pattern and period results MUST be recomputed after every saved diary and at least nightly.

### Key Entities

- **Diary day**: user, date, completed time (and whether late), foods eaten, stool details, pain, well-being, medication taken, notes, calculated index (HBI or SCCAI), red-flag outcome.
- **Diary food**: diary day, food (resolved dish or free text), approximate time of day, source (meal check or added in the diary), reactions (stomach ache, bloating, urgency, nausea).
- **Sleep record**: night (date), bedtime, wake-up time, duration, quality, late-night flag.
- **Stress record**: date, stress level 0–4.
- **Stressful period**: user, type, name, start date, end date.
- **Disease period**: user, kind (remission / flare / settling), start, end, source (proposed by the index or marked by the user), confirmation status.
- **Pattern result**: user, factor, period scope (all / remission / flare), time window, exposures, worse-day hits, comparison rate, link probability, uncertainty range, label (likely contributor / possible / not linked / not enough data), overlapping factors, computed time, engine version.
- **Flare-risk outlook**: user, date, score, level, top factors with contributions, model version.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A returning user completes the nightly diary in a median of under 2 minutes, and in under 3 minutes for 90% of diaries, in a timed walkthrough with 5 testers.
- **SC-002**: On the simulated cohort, the Pattern Finder recovers the injected contributors (food components, late nights, stress, exam periods) with precision ≥ 0.8 and recall ≥ 0.7 after 28 days of diaries, and with recall ≥ 0.8 after 60 days.
- **SC-003**: On the simulated cohort, fewer than 10% of factors that have no injected effect are labelled "likely contributor" (false-alarm rate).
- **SC-004**: Simulated flares are detected within 3 days of their injected start for ≥ 90% of flares, and ≥ 90% of days are assigned to the correct period kind.
- **SC-005**: The v1 flare-risk outlook beats the v0 rule-based score on the held-out simulated patients (higher area under the ROC curve for "flare starts within 3 days"), and both are reported in the Eval Lab with the "simulated" label.
- **SC-006**: Red-flag answers in the diary trigger escalation for 100% of the red-flag test cases (Bangla and English).
- **SC-007**: 100% of pattern sentences shown to the user match the computed numbers and pass the banned-wording check ("caused", "safe", medication advice).
- **SC-008**: Every diary screen, reminder, nudge and result is available in both Bangla and English, with no hard-coded text.

## Assumptions

- The diary replaces the separate "daily check-in" in earlier plans; one questionnaire per day.
- HBI and SCCAI are computed from patient-reported items only; items that need a clinician (e.g. abdominal mass in HBI) are scored as 0 and this is stated on screen. The index is for self-tracking, not diagnosis.
- No public dataset has daily IBD diet, sleep and stress logs, so all model validation uses the simulated cohort with injected effects. Results are labelled simulated, and real-user validation is on the roadmap.
- The personal analysis extends the existing Bayesian N-of-1 Trigger Discovery in `engine/` from food components to lifestyle factors and period scopes; the gradient-boosted outlook is trained offline (GPU or CPU batch job) and served as a versioned model file.
- The meal check (feature 002) exists and stores each checked meal so the diary can pre-fill it.
- Wearable sleep data (Health Connect, Fitbit) is out of scope for the prototype; sleep is self-reported. Wearables remain a Finals / roadmap item.
- Reminders use web push from the installed PWA; if push is unavailable the user sees the reminder when they open the app.
- The default reminder time (22:30) and the late-night rule (more than 90 minutes after the user's median bedtime, fixed 01:00 for the first week) are reasonable starting points and are configurable.
