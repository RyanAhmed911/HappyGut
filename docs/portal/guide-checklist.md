# Participants Guide check (2026-11-17)

Every requirement in the AIBC Participants Guide that applies to the Team-Built Product competition, with where HappyGut stands. Section numbers are the guide's.

**Status:** ✅ done · 🟡 partly · ⬜ open · 👤 needs the team (cannot be done from the code)

## 1. Hard requirements

| # | Guide requirement | Where | Status | Evidence / what is missing |
|---|---|---|---|---|
| 1 | 3-minute video in five fixed segments (problem 0:30, solution 0:30, demo 1:00, AI approach 0:30, impact 0:30) | §9.2 | 👤 | Script and shot list: [`video-script.md`](video-script.md). Recording and upload are the team's |
| 2 | 1-page summary | §5 | 🟡 | Draft: [`one-page-summary.md`](one-page-summary.md). Team names and the live link are blank |
| 3 | Live demo | §5, §9.1 | 👤 | App runs locally with three test accounts. Needs deployment (Hugging Face Space + Vercel) |
| 4 | Clear problem and user definition | §9.2 | ✅ | [`submission-text.md`](submission-text.md), [`../01-strategy.md`](../01-strategy.md) §3 |
| 5 | AI-native approach (LLM / RAG / Graph / ML) | §9.2 | ✅ | Vision + language model for perception and wording, food knowledge graph, cited Rule Cards, Bayesian Pattern Finder, deterministic verdict engine: [`../02-architecture.md`](../02-architecture.md) |
| 6 | Basic system flow (input → AI → output) | §9.2 | ✅ | Architecture doc; also the in-app "How it works" page |
| 7 | Initial demo or prototype | §9.2 | ✅ | Every tier-A feature in [`submission-scope.md`](submission-scope.md) works |
| 8 | Consideration for Bangla / localisation | §9.2 | ✅ | Every string in Bangla and English (CI checks parity), Bangla dish names, Bangladeshi dishes |
| 9 | Defined potential impact (KPIs or expected outcomes) | §9.2 | ✅ | Measured: [`../../evals/RESULTS.md`](../../evals/RESULTS.md). Targets: `01-strategy.md` §8 |
| 10 | **Every team member has a named role, declared in the documentation and submission** | §13.2 | 👤 | [`../00-roadmap.md`](../00-roadmap.md) still says _TBD_ for all five roles. **Mandatory** |
| 11 | Six submission components: problem, AI architecture, data and sovereignty, demo, scalability roadmap, ethical safeguards | §9.1 | 🟡 | All written across `docs/`; the one-page summary pulls them together |
| 11b | "Do not misrepresent technical capabilities" | §20.9 | ⬜ | [`submission-text.md`](submission-text.md) v3 still describes things the app does not do: speaking to it ("speaks", "Bangla speech", "voice-enabled"), a "locally hosted model" for removing identifying details (it is Presidio and rules in our backend), medication and test reminders, weight tracking, wearable signals, a generative dietitian, and hybrid retrieval over a guideline corpus. Its last paragraph lists what the prototype implements, but the body should be rewritten as v4 before it is pasted again |
| 12 | All AI usage explainable and documented | §20.4 | ✅ | [`ai-usage.md`](ai-usage.md), [`provenance.md`](provenance.md), `prompts/` |
| 13 | Legally sourced data, licences known | §15, §20.5 | 🟡 | Licences recorded in [`../03-data.md`](../03-data.md). Meal-photo datasets are still "to check" and are not used yet |
| 14 | Personal and health data anonymised | §15, §20.6 | ✅ | No real patient data anywhere. Test accounts hold sample records; PII is scrubbed before any cloud model call |
| 15 | No misleading or fabricated demos; no fake or simulated results | §15, §20.4 | 🟡 | See section 3 below: this is the rule that needs the most care |

## 2. The 100 points

| Component (20 each) | What judges look for | What we show | Gap |
|---|---|---|---|
| Innovation and AI-native design | Original, non-obvious use of AI | The model never decides: it reads the plate and words the answer; a tested engine gives the verdict. Personal Gut Graph. Pattern Finder that learns one person's contributors | None for the preliminary |
| Technical excellence and architecture | Architecture, depth, robustness, explainability | Graph + cited rules, LangGraph flow, MCP server, guard with fallback, automated tests on every change, evaluation with measured numbers | Photo-recognition accuracy not measured yet |
| Business value and commercial viability | Value proposition, path to revenue | Clinic licence, patient-support programmes, freemium: `01-strategy.md` §6 | 👤 No validation yet: talk to 3-5 gastroenterologists or dietitians and quote them |
| Global scalability and real-world impact | Scale to millions, other markets | Cuisine and language are data, not code: add dishes and a locale file. Free-tier cloud deployment | 👤 A sentence on the next market in the video |
| Responsible AI, data sovereignty and presentation | Fairness, explainability, privacy, governance | Graded verdicts (never "safe"), red-flag escalation, no medication advice, citations, PII scrub, "linked to" not "caused", results by language | 👤 Rehearsed 3-minute delivery |

**Extra credit the guide names:** at least one woman on the team (bonus points, §13.3); a polytechnic or madrasah member; an NRB or international expert with a defined role, listed in the documentation (recognised under two components, §11.1). All three are the team's to arrange.

## 3. The "no simulated results" rule

The guide prohibits "fabricated demos" and "fake or simulated results" (§20.4) and lists "ignoring real data (fake or hardcoded)" among the top mistakes (§13.4). It also requires health data to be anonymised (§20.6). HappyGut sits between these two rules, so say exactly what is real:

| Part | Real or sample | How we say it |
|---|---|---|
| Dishes, ingredients, components | Real: 61 Bangladeshi dishes | — |
| Rule Cards and citations | Real: 25 rules, each with a sentence from a published paper confirmed by DOI / PMID | "Reviewed by an LLM judge against published sources", never "clinically reviewed" |
| Verdicts | Real: computed live by the engine for whatever is typed or photographed | — |
| Photo and text understanding | Real: live model call | — |
| Patients in the test accounts | **Sample records** from a simulator, because no real patient data may be used | Notice at first entry; say "sample patient" in the video's demo segment |
| Pattern Finder results | Real computation on those sample records | "Recovered hidden contributors in a simulated cohort": always with the word *simulated* |

What would strengthen this before the finals: a team member (or a consenting patient) keeps a real diary for two weeks, shown with their permission and no identity.

## 4. Changes made in this pass

- **Evaluation run with measured numbers** (`uv run python -m happygut_api.evaluate`): Pattern Finder on 200 simulated patients, red-flag suite by language, verdict rules on the real dishes, dish-name index.
- **Two bugs the evaluation found, fixed and tested:** a dish name that contains another dish's name ("light chicken curry") could resolve to the wrong dish; two emergency phrasings were missed by the red-flag detector.
- **Video script** with timings, shots, on-screen text and the exact words to say.
- **One-page summary** draft.
- Roadmap and scope sheet brought up to date.

## 5. Open items, in order of value

1. 👤 **Name the five roles** (mandatory; a team can be disqualified from a strong score without it).
2. 👤 **Deploy** so the test credentials work for judges.
3. 👤 **Record the video** from the script.
4. 👤 **Talk to clinicians** (even two short calls) and add one quote to the summary and video.
5. 👤 **NRB advisor, woman team member, cross-institution member** if the team can arrange them; list them with roles.
6. Measure photo recognition on a small labelled set of Bangladeshi meal photos once a licensed set is chosen.
7. Voice input in Bangla (the guide suggests "Bangla UI, voice, and low-bandwidth options"). Not built: the browser's speech service sends audio to its vendor before our PII scrub can run, which conflicts with project rule 7. Needs a team decision.
8. Portal text v4 with today's features and numbers.
