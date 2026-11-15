# apps/web: HappyGut PWA

React 19 + Vite + TypeScript (strict) + Tailwind CSS v4 + Radix primitives + TanStack Query + Zod + react-i18next (Bangla and English). Installable PWA, mobile-first with a desktop layout. Hand-built in Claude Code (no Lovable export yet).

## Run it (demo mode, no accounts needed)
Two terminals, from the repo root.

Backend, with the sample patient:
```bash
cd services/api
uv sync
DEMO_MODE=true uv run uvicorn --factory happygut_api.main:app --port 8000
```
On Windows PowerShell put `DEMO_MODE=true` in the repo-root `.env` instead, then run the `uv run uvicorn …` part.

Frontend:
```bash
cd apps/web
npm install
npm run dev
```
Open http://localhost:5173 and tap **Get started**. A one-time notice explains that the account holds sample data and that HappyGut is a competition prototype, not for medical decisions; no screen carries a "simulated" label after that (the printed doctor's report keeps one footer line). The dev server proxies `/api` to the backend on port 8000. Add `GEMINI_API_KEY` to `.env` to turn on photo recognition and model-written explanations; without it, typed meals still work and explanations use the cited template.

## Screens
| Route | What it shows |
|---|---|
| `/welcome` | Landing page, language switch, one-tap entry |
| `/` | Today: flare-risk outlook with drivers, upcoming stressful period, diary status, 30-day trend, recent meal checks |
| `/check` | Photo or text → streamed dishes → verdict → cited explanation, evidence bars, gentler alternative, feedback; red-flag escalation screen |
| `/diary`, `/diary/:date` | Nightly diary in five steps: food (pre-filled from meal checks, per-food reactions), stool (Bristol chart), feeling and warning signs, sleep and stress, notes → index score |
| `/patterns` | Personal Gut Graph, then the Flare Pattern Finder for all days / remission / flares, with counts, rate bars, overlap notes and "how this works" |
| `/foods` | Food guide: every known dish with this person's verdict, searchable and filterable; Meal ideas: a week built only from dishes rated "likely OK" |
| `/gut` | Trend with flare shading, period timeline, Remission vs Flare summaries, the week before each flare, confirm / reject / mark flares, stressful periods |
| `/history`, `/history/:id` | Past meal checks with their evidence |
| `/report` | One-page pre-visit summary, printable |
| `/settings` | Health profile (diagnosis, stricture, lactose intolerance, IBS-like symptoms: verdicts change at once), language, diary reminder with a notification, safety notes |

## Structure
```
src/lib/        api.ts (fetch + SSE over POST), schemas.ts (Zod, mirrors the API), format.ts (Bangla digits, dates), i18n.ts
src/locales/    en.json, bn.json (same keys; checked by tests)
src/components/ ui/ (buttons, cards, sheets, tabs), shell.tsx, verdict.tsx, insights.tsx, TrendChart.tsx (lazy)
src/pages/      one file per screen
```

## Checks
```bash
npm run typecheck && npm test && npm run build
```
`npm test` checks that both languages have the same keys and placeholders, that every key used in the code exists, and that no string calls a food "safe" or uses causal wording.

## Production
Set `VITE_API_URL` to the backend's address (the Hugging Face Space) at build time, and add the site's origin to the backend's `CORS_ORIGINS`.

## Not done yet
- Supabase sign-in and onboarding (the app has only the demo account for now)
- Server push for the diary reminder when the app is closed (today the notification appears while the app is open or installed and running)
