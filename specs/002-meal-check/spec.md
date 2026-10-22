# Feature Specification: Meal check (hero flow)

**Feature Branch**: `002-meal-check`

**Created**: 2026-10-21

**Status**: Draft

**Input**: User description: "Meal check hero flow: photo or Bangla/English/Banglish text to a graded personal verdict with reasons, citations and an alternative"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Check a meal from a photo (Priority: P1)

A patient with IBD takes a photo of a plate of Bangladeshi food. Within seconds the app shows each recognised dish, then an overall verdict (🟢 Likely OK for you · 🟡 Caution · 🔴 Likely trigger for you · ⚪ Not sure), then a short explanation in their language. The explanation says why, cites its sources and suggests a gentler alternative.

**Why this priority**: This is the hero flow and the core of the demo video.

**Independent Test**: With the demo persona, photograph 10 seeded dishes and check that each gets the verdict expected from the knowledge layer and engine, with citations, in under 5 seconds at p90.

**Acceptance Scenarios**:

1. **Given** a clear photo of a seeded dish, **When** the patient submits it, **Then** the dish name appears first, followed by a verdict, then an explanation with at least one citation and a gentler alternative.
2. **Given** the patient's language is Bangla, **Then** all verdict and explanation text is in Bangla.
3. **Given** a blurry photo or an unknown dish, **Then** the result is ⚪ "Not sure" with a clarifying question (e.g. "Is this beef or mutton?"), never a guess.
4. **Given** a photo with no food, **Then** the app politely asks for a food photo.

---

### User Story 2 - Check a meal by typing (Priority: P1)

The patient types what they ate or plan to eat in English, Bangla or Banglish ("ajke dupure kacchi khabo"). The app resolves the dishes and gives the same kind of verdict.

**Why this priority**: Works without a camera, on low bandwidth, and for meals already eaten.

**Independent Test**: 30 typed inputs across the three languages resolve to the expected dishes and verdicts.

**Acceptance Scenarios**:

1. **Given** Banglish text naming a seeded dish, **Then** the dish is resolved and a verdict is shown.
2. **Given** text containing a phone number or name, **Then** those details are removed before any cloud AI call.

---

### User Story 3 - The verdict is personal (Priority: P1)

Two patients check the same dish and can get different verdicts. That's because the verdict uses each patient's diagnosis, phenotype (including stricturing), current state (flare or remission) and personal trigger history.

**Why this priority**: Personalisation is the core innovation (the Personal Gut Graph).

**Independent Test**: The same dish for (a) remission with no history, (b) flare, (c) stricturing Crohn's, and (d) a patient with a learned fat trigger gives the expected four verdicts.

**Acceptance Scenarios**:

1. **Given** stricturing Crohn's and a high insoluble-fibre dish, **Then** the verdict is 🔴, with the stricture rule as the stated reason.
2. **Given** a learned personal trigger with ≥ 3 exposures, **Then** the explanation names it ("4 of your last 5 high-fat meals…").

---

### User Story 4 - Red flags stop the flow (Priority: P1)

If the patient's text mentions a red-flag symptom (heavy bleeding, fever with abdominal pain, vomiting with no stool or gas, severe dehydration), the app gives no diet advice and shows an escalation screen telling them to contact a doctor or emergency care.

**Why this priority**: Safety (Constitution II).

**Independent Test**: The red-flag test suite (Bangla, English, Banglish) triggers escalation for 100% of positive cases.

---

### User Story 5 - Log the meal and give feedback (Priority: P2)

Every checked meal is saved to the patient's history with its verdict and evidence. The patient can answer "Was this right for you?" later.

**Independent Test**: After a check, the meal appears in history with its verdict, evidence IDs, model and prompt versions; feedback is stored against it.

---

### Edge Cases
- Several dishes on one plate → each dish gets its own verdict; the meal verdict is the riskiest one.
- The cloud model's free quota is used up → automatic fallback to another provider or a local model; the flow still completes.
- The GPU machine is offline (its normal state) → the standard cloud path runs fully; nothing visible changes.
- The explanation contradicts the engine verdict, or cites an ID that wasn't retrieved → it is rejected and regenerated once, otherwise a safe template is shown.
- Text inside the photo (e.g. a menu) tries to give instructions → it is treated as data only.

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: The system MUST accept a photo or text (English, Bangla, Banglish) as meal-check input.
- **FR-002**: The system MUST run the red-flag check before any other processing and stop with an escalation screen when it triggers.
- **FR-003**: The system MUST remove personal identifiers from text locally before any cloud AI call, and strip photo metadata (EXIF/GPS).
- **FR-004**: The system MUST identify dishes with a confidence value and resolve them through the knowledge layer (feature 001).
- **FR-005**: The verdict MUST be computed by the deterministic verdict engine from guideline, composition and personal evidence, never by an LLM.
- **FR-006**: The response MUST include, per dish and overall: verdict, confidence, the contribution of each evidence type, evidence IDs, and a gentler alternative where available.
- **FR-007**: The explanation MUST be generated only from the retrieved evidence, cite evidence IDs, be in the patient's language, and contain no "safe" claims or medication advice.
- **FR-008**: The response MUST stream in stages: dishes → verdict → explanation.
- **FR-009**: Low confidence or weak evidence MUST produce ⚪ "Not sure" with a clarifying question.
- **FR-010**: Each meal check MUST be stored with its evidence IDs and the model and prompt versions used.
- **FR-011**: The patient MUST be able to give "Was this right for you?" feedback on any past check.
- **FR-012**: The flow MUST work fully with the GPU machine off, and keep working when a cloud model's quota runs out.

### Key Entities
- **Patient profile**: diagnosis (CD/UC), phenotype (incl. stricturing), current state, language, known triggers.
- **Meal check**: input type, recognised dishes, per-dish and meal verdicts, scores, evidence IDs, explanation, model + prompt versions, timestamp.
- **Evidence packet**: Rule Cards, composition facts, personal trigger posteriors, guideline passages, each with an ID.
- **Feedback**: meal check ID, patient answer, time.

## Success Criteria *(mandatory)*

### Measurable Outcomes
- **SC-001**: p90 time from submit to verdict < 5 s; first content (dishes) < 2 s.
- **SC-002**: Verdict agreement with the labelled 200-food set ≥ 85%, with 🔴 recall prioritised.
- **SC-003**: Red-flag recall = 100% on the test suite.
- **SC-004**: 100% of explanations cite only retrieved evidence IDs and match the engine verdict (output guard).
- **SC-005**: Dish recognition top-3 accuracy ≥ 80% on the team's meal-photo set.
- **SC-006**: The full flow, including embeddings and reranking, completes with the GPU machine switched off, in a recorded test.

## Assumptions
- The demo persona and its history are simulated and labelled as such.
- Patient profiles are created in a short onboarding (diagnosis, phenotype, state, language).
- Voice input is out of scope for the prototype (Finals).
- Dishes outside the ~50 seeded ones get ⚪ "Not sure" and are added to the knowledge-gap list.
