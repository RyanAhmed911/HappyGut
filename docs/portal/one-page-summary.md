# HappyGut: one-page summary

**Domain:** HealthSphere AI · **Challenge:** ChronicCare AI · **Team:** _name_ · **Live demo:** _link_ · **Video:** _link_ · **Code:** github.com/RyanAhmed911/HappyGut

## Problem
Inflammatory bowel disease (Crohn's disease, ulcerative colitis) is lifelong, has no cure, and is rising fastest in newly industrialised regions including South Asia. Food triggers differ from person to person, symptoms can follow a meal by a day, and in Bangladesh most meals have no label. Patients either gamble at every meal or cut out so many foods that they risk malnutrition. Between appointments, their doctor sees none of it.

## Solution
HappyGut is a Bangla-first companion that answers "is this meal likely to trigger me?" in seconds, and learns from a two-minute nightly diary.
- **Meal check:** photo or Bangla / English text → a graded verdict per dish (likely OK · caution · likely trigger · not sure) with the reason, the cited guidance and a gentler alternative. Never "safe".
- **Nightly diary:** the day's foods, reactions, stool, sleep and stress; computes the Harvey-Bradshaw Index or SCCAI.
- **Flare Pattern Finder:** shows which foods and habits (late nights, exam weeks, missed doses) are linked to that person's worse days.
- **My Gut:** remission and flare periods kept apart, a transparent flare-risk outlook, and a one-page report for the doctor.

## AI architecture (input → AI → output)
Photo / text → **PII scrub** and **red-flag check** → **vision-language model** names the dishes → **food knowledge graph** (61 Bangladeshi dishes → gut-relevant components) and **25 cited Rule Cards** → **deterministic verdict engine** combines guidance, the food and the person's own history → **language model** words the explanation → **output guard** checks it against the engine's result (template fallback) → verdict card.
The model never decides. Personal patterns come from a Bayesian model over each person's diary. An MCP server exposes the food graph to other AI clients.

## Data and sovereignty
Only licensed sources, each recorded with its licence: open-access IBD guidance (ESPEN, IOIBD, AGA and reviews, confirmed by DOI / PMID), Wikipedia and Wikidata for dishes, USDA FoodData Central. Every rule carries an exact sentence from its paper, reviewed by an LLM judge (not by clinicians). No real patient data: the test accounts hold sample records, announced at entry. Names, phone numbers and IDs are removed inside our backend before any cloud model call; photos lose their location data. Records belong to the patient.

## Measured results
| What | Result |
|---|---|
| Pattern Finder on 200 **simulated** patients with hidden contributors, 120 days of diary | Found 293 of 409 (72%); 80% of food contributors; 52 false reports |
| Red-flag check, Bangla and English | 29 of 29 emergency phrases caught; 0 of 30 ordinary messages flagged |
| Verdict engine on 61 real dishes × 7 patient profiles | 427 of 427 reproducible; every warning cites a rule; stricture rule 11 of 11 |

Full report and how to reproduce: `evals/RESULTS.md`.

## Ethical safeguards
Graded verdicts with reasons and citations · "not sure" when evidence is missing · warning signs stop diet advice and direct the user to care · no medication advice · personal patterns are "linked to", never "caused", and need at least three occurrences · results reported by language · the app states it is not a medical device.

## Business and scale
**Clinic licence** (remote monitoring and pre-visit reports for gastroenterology clinics) is the main revenue line; **patient-support programmes** and a **freemium** patient tier follow. Beachhead: Bangladesh and the Bangla-speaking diaspora. Cuisines and languages are data, not code, so the next markets are India and Pakistan, then the wider IBD population. Runs on free-tier cloud services today.

## Roadmap
Nov–Dec 2026: deployment, real diaries from consenting users, photo-recognition accuracy on a labelled Bangladeshi set. 2027: clinic pilot in Dhaka, clinician dashboard, wearable sleep import, second cuisine.

## Team and roles
| Role | Name |
|---|---|
| Team Leader / Coordinator | _name_ |
| Business Analyst / Data Scientist | _name_ |
| UI/UX / Frontend Developer | _name_ |
| Backend / Data Engineer | _name_ |
| Presentation / Communication Lead | _name_ |
| NRB / international advisor (if any) | _name, role_ |

AI tools used to build it are documented in `docs/portal/ai-usage.md`.
