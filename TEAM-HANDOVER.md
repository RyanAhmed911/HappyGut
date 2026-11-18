# HappyGut: team handover

**Read this first if you are joining the project.** It explains what HappyGut is, what is already built, how the work follows the AIBC Participants Guide, how to run the code, and what is left to do. It was written on **18 November 2026**, when everything up to [pull request 22](https://github.com/RyanAhmed911/HappyGut/pull/22) was merged into `main`.

> ⏰ **Deadlines (AIBC Participants Guide):** the team preliminary submission closes on **Fri 20 Nov 2026**, and we plan to submit on **Thu 19 Nov**. Selection is announced on 25 Nov and the finals are on **Sat 26 Dec** at Daffodil International University. Section 8 lists what must happen before the 19th, and almost all of it needs people, not code.

---

## Contents
1. [What HappyGut is](#1-what-happygut-is)
2. [The rules we never break](#2-the-rules-we-never-break)
3. [What is built today](#3-what-is-built-today)
4. [How it works](#4-how-it-works)
5. [Getting started on your computer](#5-getting-started-on-your-computer)
6. [How we work](#6-how-we-work)
7. [How we follow the Participants Guide](#7-how-we-follow-the-participants-guide)
8. [What is left to do](#8-what-is-left-to-do)
9. [Roles](#9-roles)
10. [Where to find things](#10-where-to-find-things)
11. [Glossary](#11-glossary)

---

## 1. What HappyGut is

**One line:** a Bangla-first companion for people with Crohn's disease or ulcerative colitis that tells them, before they eat, whether a meal is likely to trigger *them*, and learns from a two-minute nightly diary.

**Competition:** International AI Builders Congress 2026 · Team-Built Product · domain **HealthSphere AI** · challenge **ChronicCare AI**.

**The problem.** Inflammatory bowel disease (IBD) is lifelong and has no cure. Food triggers differ from person to person, symptoms can follow a meal by a day, and in Bangladesh most meals (biryani at a wedding, bhorta at home) have no label. Patients either gamble at every meal or cut out so many foods that they risk malnutrition. Their doctor sees none of this between visits.

**What the app does:**

| Feature | What the user sees |
|---|---|
| **Meal check** (the "hero flow") | Photograph the plate, or type the dishes in Bangla or English. Each dish gets a graded verdict: 🟢 Likely OK for you · 🟡 Caution · 🔴 Likely trigger for you · ⚪ Not sure. Each verdict comes with the reason, the published guidance behind it and a gentler alternative. |
| **Nightly diary** | Two minutes before bed: the day's foods (meals checked earlier are already listed), which food bothered them, stool, pain, sleep, stress and doses. It computes the clinical score (Harvey-Bradshaw Index for Crohn's, SCCAI for colitis). |
| **Flare Pattern Finder** (My patterns) | Shows which foods and habits (high-fat meals, late nights, exam weeks, missed doses) are *linked to* that person's worse days, with the counts. |
| **My Gut** | Remission and flare periods kept apart on a timeline, side-by-side summaries, and stressful periods such as exams. |
| **Flare-risk outlook** | A simple points score for the next three days, with every point explained. |
| **Food guide and meal ideas** | Every dish with this person's verdict, and a week of ideas built only from dishes rated "likely OK". |
| **Doctor's report** | A one-page summary to print or show at a visit. |
| **How it works** (`/about`) | A public page for judges: the flow, the safeguards, the measured results and the data sources. |

**What makes it different.** The AI model never decides the verdict. It only reads the plate and words the explanation; a tested rules engine computes the verdict from published guidance, the food's contents and the person's own diary. That makes every answer explainable and repeatable, which is what a health product needs.

---

## 2. The rules we never break

These come from the project rules in [`.specify/memory/constitution.md`](.specify/memory/constitution.md), which the team leader approved. They apply to the code, the app text, the portal answers and the video.

1. **Never call a food "safe".** Use only the four graded verdicts.
2. **The AI never decides.** The verdict comes from the engine in `engine/`. An explanation that disagrees with the engine is replaced by a template.
3. **Evidence or "Not sure".** Every health claim cites a source. Personal patterns are "linked to" or "likely contributor", **never "caused"**, and need at least 3 occurrences.
4. **Warning signs come first.** Heavy bleeding, fever with stomach pain, signs of a blocked bowel or severe dehydration stop all food advice and send the person to a doctor.
5. **No medication advice.** Never suggest starting, stopping or changing a medicine.
6. **Privacy.** Names, phone numbers and ID numbers are removed in our backend before any cloud AI call. **No real patient data anywhere. No secrets in git.**
7. **Bangla and English for every screen.** No hard-coded text; every string is in both `apps/web/src/locales/en.json` and `bn.json`. Supported input is Bangla and English (not Banglish sentences).
8. **Free tiers only, no card.** No Google Cloud / Vertex, AWS or paid domains.
9. **Licensed data only**, with each licence recorded in [`docs/03-data.md`](docs/03-data.md).
10. **Say what is real.** The knowledge was reviewed by an **LLM judge**, never "clinically reviewed". Results on simulated patients are always called **simulated**. Nothing in the video or portal may claim a feature the app doesn't have.

---

## 3. What is built today

Everything below works when you run the app locally (section 5). Nothing is deployed online yet.

| Area | Status | Notes |
|---|---|---|
| Meal check (typed, Bangla or English) | ✅ Works | |
| Meal check (photo) | ✅ Works with a Gemini key | Confirmed on 15 Nov with real keys |
| Red-flag check and escalation screen | ✅ | 29 of 29 test phrases caught |
| Stricture safety rules | ✅ | Applied before any AI output |
| Nightly diary, sleep, stress, stressful periods | ✅ | |
| Flare Pattern Finder, remission / flare periods, flare-risk outlook | ✅ | |
| Food guide, meal ideas, doctor's report, meal history | ✅ | |
| Sign-in with three test accounts for judges, restore records | ✅ | See [`docs/portal/test-credentials.md`](docs/portal/test-credentials.md) |
| Health profile editing (stricture, lactose intolerance, IBS-like symptoms) | ✅ | Verdicts change immediately |
| Personal Gut Graph view | ✅ | On My patterns |
| "How it works" public page | ✅ | `/about` |
| Bangla and English throughout | ✅ | A test checks both files have the same keys |
| Knowledge layer: 61 Bangladeshi dishes, 25 cited Rule Cards | ✅ | All reviewed by an LLM judge against retrieved sentences from papers |
| Evaluation with measured numbers | ✅ | [`evals/RESULTS.md`](evals/RESULTS.md) |
| Food-graph MCP server | ✅ | `services/mcp` |
| Automated tests and CI | ✅ | About 250 tests; every pull request runs them, plus a secret scan |
| **Deployment (public link)** | ❌ **Not done** | Needed for judges; see section 8 |
| Supabase sign-up for real users | ❌ | The test accounts live in memory |
| Diary saved in Postgres | ❌ | Database tables exist; diary storage on Postgres is not written |
| Loading the knowledge into Neo4j / Supabase | ❌ | The app reads the seed files directly |
| Langfuse tracing, n8n workflows, push notifications | ❌ Designed only | |
| Guideline corpus with retrieval (RAG) | ❌ Designed only | Rule Cards carry the cited sentences instead |
| LightGBM flare model, wearables, voice, federated learning | ❌ Roadmap | |

**The test accounts** hold sample patient records made by a simulator, because real patient data may not be used. The app says so once when you first sign in.

| Account | Patient |
|---|---|
| `nusrat@happygut.test` | Crohn's disease, in remission, four months of records, exams in 3 days. **Use this one for the video.** |
| `rafi@happygut.test` | Ulcerative colitis, eight days into a flare |
| `ayesha@happygut.test` | Crohn's with a stricture, brand-new user with no records |

Passwords are not in the repository. Each person sets their own in `.env` (section 5).

---

## 4. How it works

```
 Photo or text (Bangla / English)
        │
        ▼
 PII scrub + red-flag check ──── warning sign? ──► stop, send to a doctor
        │
        ▼
 Vision-language model (Gemini) names the dishes          ← AI: perception only
        │
        ▼
 Knowledge layer: dish → components (fat, lactose, fibre, spice…)
                  + Rule Cards with sentences from published IBD guidance
                  + this person's patterns from their diary
        │
        ▼
 Verdict engine (engine/, pure Python, unit-tested)       ← decides the verdict
        │
        ▼
 Language model words the explanation (Gemini, Groq fallback)
        │
        ▼
 Output guard: text must agree with the engine, else a template is used
        │
        ▼
 Verdict card in the app (React PWA)
```

**Tech stack**

| Layer | Technology |
|---|---|
| Web app | React 19, Vite, TypeScript (strict), Tailwind CSS, TanStack Query, Zod, react-i18next; installable as a PWA |
| Backend | Python 3.11, FastAPI, LangGraph flow, Pydantic-AI agents, server-sent events for the live result |
| AI models | Gemini Flash-Lite / Flash via Google AI Studio (free key), Groq as fallback. Model names are checked at start-up |
| Privacy | Presidio plus Bangladesh-specific rules, in our own backend |
| Engine | Pure Python, no network: verdicts, red flags, clinical scores, periods, Pattern Finder (Bayesian), flare risk, patient simulator |
| Knowledge | YAML seed files in `data/seeds/`, reviewed by an LLM judge (`data/review/llm_judge/`) |
| Database (designed, partly used) | Supabase Postgres with migrations and row-level security, Neo4j for the food graph |
| CI | GitHub Actions: engine, pipelines, MCP, API, web, database tests; GitGuardian secret scan |

The full design, including the parts not built yet, is in [`docs/02-architecture.md`](docs/02-architecture.md). **Read section 3 above for what is real**: the architecture document describes the target, not today's state.

**Repository map**

```
apps/web/           The web app (pages in src/pages, text in src/locales)
services/api/       FastAPI backend: meal-check flow, diary, insights, sign-in, evaluation
services/mcp/       Food-graph MCP server
engine/             Verdict engine, red flags, Pattern Finder, periods, simulator (pure Python)
pipelines/          Seed validator, knowledge graph, dish search
data/seeds/         Dishes and Rule Cards (YAML), the knowledge the app uses
data/review/        LLM-judge review records and the evidence quotes
evals/              Evaluation report (RESULTS.md) and test sets
supabase/           Database migrations and their tests
prompts/            Runtime prompts (versioned) and the prompts used to build the project
specs/              Feature specs: 001 knowledge layer, 002 meal check, 003 personal layer
docs/               Strategy, architecture, data, setup, and docs/portal (submission texts)
.specify/           Project rules (constitution)
AGENTS.md           Instructions for AI coding assistants (Claude Code, Cursor, Codex…)
```

---

## 5. Getting started on your computer

You don't need any of the online accounts to run the app: **demo mode** runs everything on your computer with the three test accounts.

### Tools (Windows, PowerShell)
```powershell
winget install Git.Git GitHub.cli OpenJS.NodeJS.LTS Microsoft.VisualStudioCode
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
Close and reopen PowerShell. (macOS / Linux: install Git, Node.js 22 and [uv](https://docs.astral.sh/uv/).)

### Get the code
Ask the team leader to add you as a collaborator on GitHub, then:
```powershell
gh auth login
gh repo clone RyanAhmed911/HappyGut
cd HappyGut
Copy-Item .env.example .env
```

### Fill in `.env`
For demo mode you need only these lines (choose your own throw-away passwords):
```
DEMO_MODE=true
TEST_PASSWORD_NUSRAT=pick-one
TEST_PASSWORD_RAFI=pick-another
TEST_PASSWORD_AYESHA=and-another
```
For photo checks and AI-written explanations, add a Gemini key. Get your own free one at aistudio.google.com → **Get API key** (not Google Cloud). A Groq key (console.groq.com) adds the fallback model.
```
GEMINI_API_KEY=...
GROQ_API_KEY=...
```
> **Never commit `.env`, and never paste a key into chat, email, an issue or a pull request.** If you need one of the team's shared keys (Supabase, Neo4j…), ask the team leader privately.

### Run the app
Terminal 1, the backend:
```powershell
cd services/api
uv sync
uv run uvicorn --factory happygut_api.main:app --port 8000
```
Terminal 2, the web app:
```powershell
cd apps/web
npm install
npm run dev
```
Open http://localhost:5173 and sign in as `nusrat@happygut.test` with the password you chose. Restarting the backend resets the sample records.

**If photo checks fail:** run `uv run python -m happygut_api.diagnose` in `services/api`. It tries each model on its own and prints the reason, without printing keys.

### Run the tests
```powershell
cd engine;       uv run --group dev pytest -q; cd ..
cd pipelines;    uv run python -m happygut_pipelines.seeds; uv run --group dev pytest -q; cd ..
cd services/mcp; uv run --group dev pytest -q; cd ../..
cd services/api; uv run --group dev pytest -q; cd ../..
cd apps/web;     npm run typecheck; npm test; npm run build; cd ../..
```

### Re-run the evaluation
```powershell
cd services/api
uv run python -m happygut_api.evaluate                # about 6 minutes; 200 simulated patients
uv run python -m happygut_api.evaluate --patients 40  # quicker check
```
It rewrites `evals/RESULTS.md`, `evals/summary.json` and the numbers shown on the app's "How it works" page.

More detail on accounts and setup: [`docs/setup.md`](docs/setup.md).

---

## 6. How we work

**Branches and pull requests**
1. Make a branch from `main` for each piece of work: `git checkout -b yourname/short-topic`.
2. Commit small, clear changes. Run the tests for the part you changed.
3. Push and open a pull request into `main`. Describe what changed and how you tested it.
4. CI runs every test suite and a GitGuardian secret scan. **Merge only when everything is green.** Never disable or skip a test to make it pass.
5. One pull request per step of work. Record decisions in the decision log of the relevant `docs/` file.

**Changing things safely**

| You want to… | Do this |
|---|---|
| Change any text in the app | Edit **both** `apps/web/src/locales/en.json` and `bn.json`. A test fails if keys or placeholders differ, or if the text says "safe" or "caused". |
| Add or fix a dish | Follow `.claude/skills/add-dish/SKILL.md`; run the seed validator (`uv run python -m happygut_pipelines.seeds` in `pipelines/`) |
| Add a Rule Card | Follow `.claude/skills/add-rule-card/SKILL.md`. It needs a real paper (DOI or PMID) and an exact sentence from it. **Never invent a quote or an identifier.** |
| Change an AI prompt | Add a new version in `prompts/runtime/`; follow `.claude/skills/new-prompt-version/SKILL.md` |
| Change the engine, prompts, models or knowledge | Re-run the evaluation and check the red-flag suite still catches every phrase |
| Change the database | Write a migration in `supabase/migrations/` (Supabase CLI); never edit the live database by hand |

**AI coding assistants.** Most of the code was built with Claude Code, and the guide encourages AI-native tools. Whichever assistant you use (Claude Code, Cursor, Codex, Lovable…), it should read [`AGENTS.md`](AGENTS.md) first; that file is the shared instruction set. You are still responsible for checking what the assistant writes. Record the AI tools you use in [`docs/portal/ai-usage.md`](docs/portal/ai-usage.md).

**Words to use and avoid**

| Say | Don't say |
|---|---|
| "likely OK for you", "likely trigger for you" | "safe", "dangerous" |
| "linked to your worse days", "likely contributor" | "causes", "caused" |
| "reviewed by an LLM judge against published sources" | "clinically reviewed", "doctor-approved", "validated" |
| "recovered 72% of hidden triggers **in simulated patients**" | "72% accurate", "predicts flares" |
| "sample patient records" | "real patient", "our users" |
| "competition prototype, not a medical device" | anything that sounds like a diagnosis or treatment |

---

## 7. How we follow the Participants Guide

The full requirement-by-requirement check is in [`docs/portal/guide-checklist.md`](docs/portal/guide-checklist.md). In short:

### What the preliminary round requires (§9.2)

| Requirement | Where we stand |
|---|---|
| 3-minute video: problem 0:30 · solution 0:30 · demo 1:00 · AI approach 0:30 · impact 0:30 | Script ready: [`docs/portal/video-script.md`](docs/portal/video-script.md). **Not recorded.** |
| Clear problem and user definition | ✅ [`docs/portal/submission-text.md`](docs/portal/submission-text.md), [`docs/01-strategy.md`](docs/01-strategy.md) |
| AI-native approach (LLM / RAG / graph / ML) | ✅ Vision + language models, knowledge graph with cited rules, Bayesian Pattern Finder, deterministic engine |
| Basic system flow (input → AI → output) | ✅ Section 4 above and the app's "How it works" page |
| Working demo or prototype | ✅ Runs locally. **Needs deployment** so judges can use it |
| Bangla / localisation | ✅ Every screen in Bangla and English; Bangladeshi dishes; Bangla dish names |
| KPIs or expected outcomes | ✅ Measured: [`evals/RESULTS.md`](evals/RESULTS.md). Targets: `docs/01-strategy.md` §8 |
| 1-page summary | Draft: [`docs/portal/one-page-summary.md`](docs/portal/one-page-summary.md). Names and links blank |
| Test login for judges | ✅ Three accounts; the rows to enter are in [`docs/portal/test-credentials.md`](docs/portal/test-credentials.md) |
| **A named role for every team member** (§13.2, mandatory) | ❌ **Not done.** See section 9 |

### How judges score (§11: five parts, 20 points each)

| Part | What we show | Weak spot |
|---|---|---|
| Innovation and AI-native design | The AI reads and explains but never decides; a personal pattern model per patient; a Bangladeshi food graph | — |
| Technical excellence and architecture | Cited rules, LangGraph flow, MCP server, output guard, about 250 tests, measured evaluation | Photo accuracy not measured |
| Business value and commercial viability | Clinic licence first, then patient-support programmes and a freemium tier (`docs/01-strategy.md` §6) | **No validation yet:** we need quotes from 2–3 gastroenterologists or dietitians |
| Global scalability and impact | New cuisines and languages are data, not code; free-tier cloud deployment | Say the next markets clearly in the video |
| Responsible AI, data sovereignty and presentation | Graded verdicts, red-flag escalation, no medication advice, PII scrub, honest wording | A rehearsed, confident 3-minute delivery |

**Extra credit the guide names (§13.3):** at least one woman on the team (bonus points), a polytechnic or madrasah member, and an NRB or international expert with a defined, documented role.

### The rule that needs the most care
The guide forbids "fabricated demos" and "fake or simulated results" (§20.4) but also requires health data to be anonymised (§20.6). So we use **sample patients** for the demo and **always say so**. The dishes, rules, citations and verdicts are real and computed live; only the patients' histories are simulated. Keep this wording in everything you write or record.

### The measured numbers (from `evals/RESULTS.md`, 17 Nov)

| What | Result |
|---|---|
| Pattern Finder on 200 **simulated** patients with hidden triggers, 120 days of diary | Found 293 of 409 (72%); 80% for food triggers; 52 false reports |
| Red-flag check, Bangla and English | 29 of 29 emergency phrases caught; 0 of 30 ordinary messages flagged |
| Verdict engine, 61 dishes × 7 patient profiles | 427 of 427 identical when repeated; every warning cites a rule; stricture rule 11 of 11 |
| Not measured yet | Photo recognition accuracy, agreement with a dietitian, anything on real patients |

---

## 8. What is left to do

### A. Before we submit (19 Nov; hard deadline 20 Nov)

| # | Task | Suggested owner | How |
|---|---|---|---|
| 1 | **Fill in the five roles** with names | Team Leader | Table in section 9; then update `docs/00-roadmap.md` and `docs/portal/one-page-summary.md` |
| 2 | **Deploy the app** so the judges' logins work | Backend + Frontend | Backend: Hugging Face Space (Docker; `services/api/Dockerfile`, port 7860). Set Space secrets `DEMO_MODE=true`, `GEMINI_API_KEY`, `GROQ_API_KEY`, the three `TEST_PASSWORD_*`, `SESSION_SECRET` and `CORS_ORIGINS=["https://<your-vercel-app>.vercel.app"]`. Frontend: Vercel, root directory `apps/web`, environment variable `VITE_API_URL=https://<your-space>.hf.space` (no `/v1`; the app adds it), and a `vercel.json` rewrite of every path to `/index.html` so links like `/about` open directly. Test sign-in on a phone. Write the steps into `docs/setup.md` as you go. |
| 3 | **Enter the test credentials** in the portal | Team Leader | Three rows from `docs/portal/test-credentials.md`, same passwords as the Space secrets |
| 4 | **Record the 3-minute video** | Presentation Lead | Follow `docs/portal/video-script.md` exactly: timings, Bangla screens, a "Sample patient records" caption during the demo. Upload the same file to YouTube and Facebook |
| 5 | **Rewrite the portal text (v4)** | Presentation Lead + Business Analyst | `docs/portal/submission-text.md` (v3) still describes things the app doesn't do: talking to it by voice, a locally hosted name-removal model, medication and test reminders, weight tracking, wearables, a meal-plan-writing dietitian, guideline retrieval. Rewrite to match section 3, keep each section at least as long as before, and add the measured numbers with the right wording |
| 6 | **Finish the one-page summary** | Presentation Lead | `docs/portal/one-page-summary.md`: team name, roles, links |
| 7 | **Reconcile the portal ticks** | Team Leader | Checklist in `docs/portal/submission-scope.md` §4: untick everything marked C (not built), e.g. CrewAI, smolagents, DSPy, fine-tuning, n8n, Langfuse, the Eval Lab |
| 8 | **Talk to 2–3 clinicians** (even 10-minute calls) | Business Analyst | Ask: would a pre-visit report help? Is the verdict wording right? Get permission to quote one sentence. Add it to the summary and video |
| 9 | Make the repository public and check git history has no keys | Team Leader | The secret scan has been clean on every pull request |

### B. After selection, before the finals (25 Nov → 26 Dec)

| Task | Where to start |
|---|---|
| Real sign-up with Supabase Auth, and diary storage in Postgres | `services/api/src/happygut_api/store.py` (`PostgresStore`), `supabase/migrations/`, spec 003 |
| Load the knowledge into Neo4j and Supabase | `pipelines/`, spec 001 task T013 |
| Measure photo recognition on a licensed, labelled set of Bangladeshi meal photos | Candidate datasets in `docs/03-data.md` (licences still "to check") |
| A dietitian-labelled verdict set, to measure agreement | `evals/`, `.claude/skills/run-evals` |
| Lower the Pattern Finder's false reports; detect missed doses better (5% today) | `engine/src/happygut_engine/patterns.py`; re-run the evaluation |
| Real diaries from consenting team members for two weeks (no identity shown) | Would answer the "simulated" concern directly |
| Push reminders for the nightly diary | `apps/web/src/lib/reminder.ts` |
| Langfuse tracing, LightGBM flare model | `docs/02-architecture.md`, `docs/portal/submission-scope.md` |
| Bangla voice input | **Needs a decision first:** the browser's speech service sends audio to its vendor before our privacy step runs, which breaks rule 6 |
| Rehearse the 3-minute live pitch (5-minute slot: 1 transition, 3 pitch, 1 scoring) | Guide §9.3 |

---

## 9. Roles

The guide makes this **mandatory** (§13.2): every member has a named role, declared in the documentation and the submission. One person may hold more than one role.

| Official role | Name | Leads |
|---|---|---|
| Team Leader / Coordinator | _____ | Scope decisions, integration, portal, merges |
| Business Analyst / Data Scientist | _____ | KPIs, clinician interviews, business model, evaluation, Pattern Finder |
| UI/UX / Frontend Developer | _____ | Web app, Bangla text, accessibility, deployment on Vercel |
| Backend / Data Engineer | _____ | API, AI models, database, knowledge loading, deployment on Hugging Face |
| Presentation / Communication Lead | _____ | Video, one-page summary, portal text, pitch rehearsal |
| NRB / international advisor (optional, extra credit) | _____ | Architecture or product advice, documented |

---

## 10. Where to find things

| Need | File |
|---|---|
| The rules | [`.specify/memory/constitution.md`](.specify/memory/constitution.md) |
| Instructions for AI assistants | [`AGENTS.md`](AGENTS.md) |
| Plan, dates and status | [`docs/00-roadmap.md`](docs/00-roadmap.md) |
| Strategy, personas, business model, KPIs, decision log | [`docs/01-strategy.md`](docs/01-strategy.md) |
| Architecture (target design) | [`docs/02-architecture.md`](docs/02-architecture.md) |
| Data sources and licences | [`docs/03-data.md`](docs/03-data.md) |
| Accounts and setup | [`docs/setup.md`](docs/setup.md) |
| How the LLM judge reviews knowledge | [`docs/seed-review.md`](docs/seed-review.md), records in `data/review/llm_judge/` |
| Guide requirements and status | [`docs/portal/guide-checklist.md`](docs/portal/guide-checklist.md) |
| What is real vs designed (portal ticks) | [`docs/portal/submission-scope.md`](docs/portal/submission-scope.md) |
| Portal texts | `docs/portal/submission-text.md`, `data-lifecycle.md`, `ai-usage.md`, `provenance.md` |
| Video script | [`docs/portal/video-script.md`](docs/portal/video-script.md) |
| One-page summary | [`docs/portal/one-page-summary.md`](docs/portal/one-page-summary.md) |
| Judges' logins | [`docs/portal/test-credentials.md`](docs/portal/test-credentials.md) |
| Evaluation results | [`evals/RESULTS.md`](evals/RESULTS.md) |
| Feature specs | `specs/001-knowledge-layer`, `specs/002-meal-check`, `specs/003-personal-layer` |

---

## 11. Glossary

| Term | Meaning |
|---|---|
| **IBD** | Inflammatory bowel disease: Crohn's disease (CD) and ulcerative colitis (UC) |
| **Flare / remission** | A period of active symptoms / a calm period |
| **Stricture** | A narrowed part of the bowel in some Crohn's patients; skins, seeds, nuts and tough fibre can block it, so the app has hard rules for it |
| **HBI / SCCAI** | Harvey-Bradshaw Index (Crohn's) and Simple Clinical Colitis Activity Index (colitis): standard symptom scores the diary computes |
| **Bristol scale** | A 1–7 scale for stool type |
| **FODMAP** | Fermentable carbohydrates (fructans, GOS, polyols…) that bother some people with IBS-like symptoms |
| **Rule Card** | One cited rule, e.g. "high fat in a flare → caution", with the paper and the exact sentence it relies on (`data/seeds/rule_cards/`) |
| **LLM judge** | An AI model that checks each rule and dish against retrieved sources using a written rubric. It replaces expert review in this prototype, and we always say so |
| **Verdict engine** | The deterministic Python code that computes the verdict (`engine/`) |
| **Pattern Finder** | The Bayesian model that compares how often a worse day follows each food or habit, against the person's other days |
| **Personal Gut Graph** | The picture of what one person's diary links to their worse days |
| **Hero flow** | Photo or text → verdict → logged meal → updated patterns. The product's core; protect it above everything |
| **Tier A / B / C** | Real and working / real but minimal / designed only (never shown as working) |
| **Demo mode** | `DEMO_MODE=true`: the backend runs with three in-memory test accounts holding sample records |
| **MCP** | Model Context Protocol: lets other AI tools query our food graph |
| **PII** | Personally identifying information (names, phone numbers, ID numbers) |

---

*Questions: ask the team leader. If something in this file is out of date, fix it in a pull request.*
