# What's new since the team handover (18 November 2026)

This covers everything merged after [`TEAM-HANDOVER.md`](TEAM-HANDOVER.md) was written: pull requests 24 to 31. Read the handover first if you're new; this file only adds to it.

| # | Change | Where | Needs setup? |
|---|---|---|---|
| 1 | Video script v2.1 with the team's story and verified sources | `docs/portal/video-script.md` | No |
| 2 | Portal text v5.1, every claim checked against the app | `docs/portal/submission-text.md` | No (paste it) |
| 3 | **Weight tracking** with a weight-loss notice | My Gut, Today, doctor's report | No |
| 4 | **Medicines & tests**: own schedule, dose ticks, reminders | New "Medicines & tests" page, Today, diary, report | Only to allow notifications in the browser |
| 5 | **Three more MCP servers**: guidelines, evals, journal | `services/mcp` | Optional |
| 6 | **Langfuse tracing** | backend | Yes: two keys |
| 7 | **n8n workflows**: health check, nightly job, safety check, failure email | `n8n/` | Yes: Docker and a token |
| 8 | **Machine-learning flare model (LightGBM)** | flare-risk card | Only to install it (one command) |

Part A explains each change. Part B is the step-by-step setup. Part C covers deployment, Part D the portal and video, Part E troubleshooting.

---

# Part A: What changed

## 1. Video script v2.1 (`docs/portal/video-script.md`)
- **Story:**
  - IBD is rising fast in South Asia and few people here know it.
  - Crohn's is often first treated as TB, and diagnosis takes about a year.
  - There is no cure and no known cause, and triggers differ for every patient.
  - HappyGut learns each patient's own triggers.
  - With consent, anonymised data could help research and let Bangladesh contribute.
- **Structure:** follows the portal's "YouTube Video Guidance" segment by segment.
- **Inside the file:** narration timed to about 2.5 words a second, a shot list, who does what, free tools, a two-day schedule, and the YouTube / Facebook description.
- **Facts:** every fact is quoted exactly from a published paper (section 7 of the file). Use only those.

## 2. Portal text v5.1 (`docs/portal/submission-text.md`)
- Built from a teammate's v5 draft, with each claim checked against the code.
- It now also describes weight tracking, medicines and tests, and the machine-learning model, with their real numbers.
- Paste only the text under each heading, not the note at the top.

## 3. Weight tracking
- **Logging:** on **My Gut → Weight**, log your weight; once a week is enough.
- **What you see:** a chart, your latest weight, the change over 30, 90 and 180 days, and your recent weigh-ins (each can be deleted).
- **Weight-loss notice:** if your weight falls **more than 5% below your highest weigh-in in the last 6 months** (or more than 10% over 6–12 months), the app says *"Your weight is down X% since [date]… please tell your doctor"*.
  - The threshold is the published GLIM criterion (Cederholm et al. 2019, PMID 30920778).
  - It never says "malnutrition" and never gives advice.
- **Today:** shows the notice, or a "Weekly weigh-in" reminder when a week has passed since the last one.
- **Doctor's report:** latest weight, the change over the report period, and the notice.
- **Test accounts:** Rafi crosses the threshold during his flare; Nusrat is stable; Ayesha has no weigh-ins yet.

## 4. Medicines & tests
- **New page:** "Medicines & tests" in the sidebar (or **Manage** on Today's card).
- **Medicines:** name, up to 4 times a day, how often (every day, weekly, or every 2 to 8 weeks for injections and infusions), and a note.
- **Tests and appointments:** blood test, stool test, colonoscopy, scan, doctor visit or other, with a date and an optional time.
- **Today:** shows the day's doses with a "Mark taken" button, and the next test within two weeks.
- **Nightly diary:** shows "you ticked 1 of 2 doses for this day" under the dose question.
- **Doctor's report:** lists the medicines as entered and the upcoming tests.
- **Reminders:**
  - Switch them on on the Medicines page; the browser asks permission.
  - A dose reminder comes at its time; a test reminder comes the evening before (from 20:00) and the morning of the test (from 07:30).
  - **They only appear while HappyGut is open or installed on the phone.** Reminders to a closed app need a server and are on the roadmap.
- **Safety:** the app only repeats what the patient entered. There is no drug list and no dose advice. After a missed dose it says to ask the doctor or pharmacist.
- **Test accounts:**
  - Nusrat: Azathioprine and Vitamin D, a blood test in 5 days, a doctor visit in 12 days.
  - Rafi: Mesalamine twice a day, a stool test in 2 days, a doctor visit in 6 days.
  - Ayesha: nothing yet.

## 5. MCP servers (`services/mcp`)
There are now four read-only servers that other AI tools (Claude Desktop, Claude Code, a clinician's assistant) can use.

| Server | Tools | Reads |
|---|---|---|
| `happygut-foodgraph` (existing) | `search_dish`, `get_components`, `explain_verdict_path` | Dishes and Rule Cards |
| `happygut-guidelines` | `search_rules`, `get_rule`, `list_sources` | The 25 Rule Cards with their papers and exact quotes |
| `happygut-evals` | `get_results`, `pattern_recovery`, `check_red_flags` | `evals/summary.json`, plus a red-flag check on any message |
| `happygut-journal` | `get_overview`, `get_recent_days`, `get_patterns` | **One** patient's records, using that patient's own sign-in token. Never returns their name, notes or photos |

## 6. Langfuse tracing
- **What it records:** every meal check becomes one trace in Langfuse:
  - the steps and how long each took;
  - the verdict and the engine version;
  - whether the explanation came from the AI or the template;
  - the AI calls nested inside, with their timing and token counts.
- **What it never sends:** photos, names (text is scrubbed before any AI call) or patient ids (a one-way code is used instead).
- **When it runs:** off until both Langfuse keys are set.

## 7. n8n workflows (`n8n/workflows`)

| Workflow | When | What it does |
|---|---|---|
| `happygut-health.json` | every 30 minutes | Calls `/v1/health`. **Keeps the free Hugging Face Space awake for judges** and fails if the knowledge isn't fully loaded |
| `happygut-nightly.json` | 23:30 Dhaka time | Calls `POST /v1/jobs/nightly`: refreshes every patient's insights and records counts only (no names) |
| `happygut-safety-check.json` | Mondays 07:10 | Calls `POST /v1/jobs/selfcheck`: re-runs the red-flag suite, verdict checks, stricture rule and dish names on the live app |
| `happygut-alert.json` | when one of the above fails | Optional: emails the team |

The two job endpoints are protected by a separate `JOBS_TOKEN`, and are switched off when it isn't set.

## 8. Machine-learning flare model (LightGBM)
- **What it predicts:** whether a new flare starts within 3 days, from 24 diary inputs.
- **Training:** only on 200 simulated patients.
- **Results:** on 50 simulated patients it never saw, ROC AUC **0.658**, against 0.558 for the rule-based score. When it flags the riskiest 10% of days, it catches **31%** of flare starts, against 11% for the rule-based score. Full report: `evals/FLARE_MODEL.md`.
- **In the app:** the flare-risk card has a new **"Machine-learning estimate"** section under the existing score. It shows a level and the three things that raised it most (exact SHAP values).
- **When it pauses:** during a flare (Rafi), and until there are two weeks of diary (Ayesha).
- **Labelling:** the card says it was trained on simulated patients and is not a diagnosis.
- **If it isn't installed:** the card simply shows the rule-based score alone.

---

# Part B: Set it up, step by step (Windows, PowerShell)

Everything below assumes the repository is at `D:\Headshot\HappyGut\HappyGut`; change the path if yours differs. Commands that run in a folder say which one.

## Step 1: Get the latest code
In the repository root:
```powershell
git checkout main
```
```powershell
git pull origin main
```

## Step 2: Add the new lines to `.env`
Open `.env` in the repository root (`code .env`) and add these lines. Keep your existing ones.

```
# Langfuse (step 5). Leave empty to keep tracing off.
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com

# n8n jobs (step 6): any random string of at least 24 characters
JOBS_TOKEN=
HAPPYGUT_API_URL=http://host.docker.internal:8000
HAPPYGUT_ALERT_FROM=
HAPPYGUT_ALERT_TO=
```

Make a random value for `JOBS_TOKEN` (and for `N8N_ENCRYPTION_KEY` if it's still empty):
```powershell
python -c "import secrets;print(secrets.token_urlsafe(32))"
```

- **Langfuse host:** if your Langfuse project is in the US region, use `https://us.cloud.langfuse.com`. The project page shows which one.
- **Never commit `.env`**, and never paste keys into chat, an issue or a pull request.

## Step 3: Install the backend with the new parts
In `services\api`:
```powershell
uv sync --extra tracing --extra ml
```

| Extra | What it adds |
|---|---|
| `tracing` | Langfuse tracing |
| `ml` | The flare model (LightGBM) |
| `pii` (optional, already existed) | Presidio name detection. It downloads a small spaCy model from GitHub |

- **Windows only:** LightGBM needs the Microsoft Visual C++ Redistributable. Most PCs already have it. If step 4 shows an error mentioning `lib_lightgbm.dll` or `vcomp140.dll`, install it from Microsoft ("Latest supported Visual C++ Redistributable downloads", x64) and run the command again.

## Step 4: Run the app
**Terminal 1**, in `services\api`:
```powershell
uv run --extra tracing --extra ml uvicorn --factory happygut_api.main:app --port 8000
```
Keep the `--extra` flags on `uv run` too, so the extras stay installed.

**Terminal 2**, in `apps\web`:
```powershell
npm install
```
```powershell
npm run dev
```

Open http://localhost:5173 and sign in as `nusrat@happygut.test`. Then check:

| Where | What you should see |
|---|---|
| Today, flare-risk card | Under the score, **"Machine-learning estimate"**: *High chance of a new flare*, top reason *a stressful period starts soon* |
| Today | A **Medicines & tests** card with Azathioprine and Vitamin D, and "Blood test · In 5 days" |
| Sidebar → Medicines & tests | Doses, medicines, tests, and two reminder switches |
| My Gut → Weight | A stable weight chart |
| Sign out, then sign in as `rafi@happygut.test` | A weight-loss notice on Today and My Gut. The ML section says it's paused because he's in a flare |

**To check that the model loaded**, open http://127.0.0.1:8000/v1/insights/flare-risk while signed in, or look at the card. If the card shows no "Machine-learning estimate" section, the `ml` extra isn't installed (see step 3).

**To try reminders:** on Medicines & tests, switch on "Remind me at each dose time" and allow notifications when the browser asks. Then add a medicine with a time one or two minutes ahead and keep the tab open.

## Step 5: Langfuse (tracing)
1. Sign in at cloud.langfuse.com and open your HappyGut project. If you don't have one, create it; the Hobby plan is free.
2. Go to **Settings → API Keys → Create new API keys**. Copy the **public key** (`pk-lf-…`) and the **secret key** (`sk-lf-…`) into `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` in `.env`.
3. Restart the backend (Terminal 1: `Ctrl+C`, then the step 4 command again). The window should print `tracing to Langfuse at https://cloud.langfuse.com`.
4. Check http://127.0.0.1:8000/v1/health: it should show `"tracing": true`.
5. Do a meal check in the app. Within about a minute, a trace called **meal_check** appears in Langfuse under **Tracing**. With a Gemini key set, the AI calls appear nested inside it.

Only real meal checks are traced; the sample history created at start-up is not.

## Step 6: n8n (scheduled workflows)
You need **Docker Desktop** for Windows (free). Install it, start it, and wait until it says it's running.

1. Make sure `.env` has `N8N_ENCRYPTION_KEY` and `JOBS_TOKEN` (step 2).
2. Start the backend (step 4) **after** adding `JOBS_TOKEN`, so the job endpoints are switched on.
3. Start n8n. In the repository root:
   ```powershell
   docker compose up -d
   ```
4. Import the four workflows:
   ```powershell
   docker compose exec n8n n8n import:workflow --separate --input=/workflows
   ```
5. Open http://localhost:5678 and create your n8n owner account; it's local only.
6. Create the token credential:
   1. **Credentials → Add credential → Header Auth**.
   2. Name it exactly **`HappyGut jobs token`**.
   3. Field **Name**: `Authorization`. Field **Value**: `Bearer ` followed by your `JOBS_TOKEN`, with one space after "Bearer".
   4. Save.
7. Open **HappyGut: nightly refresh**. Double-click the **Nightly job** node and select *HappyGut jobs token* under Credential. Do the same for the **Self-check** node in **HappyGut: weekly safety self-check**. The health workflow needs no credential.
8. In each workflow, press **Test workflow**:
   - **Health:** ends at "All good".
   - **Nightly:** ends at "Summary" with counts (3 patients, 1 in a flare, 1 weight notice…).
   - **Safety check:** ends at "All good".
9. Switch each workflow to **Active** (top right).
10. **Optional failure emails:**
    1. Create an **SMTP** credential named **`HappyGut alert email`**. For Gmail: host `smtp.gmail.com`, port 465, SSL on, your address, and an *app password*.
    2. Set `HAPPYGUT_ALERT_FROM` and `HAPPYGUT_ALERT_TO` in `.env`, then run `docker compose up -d` again.
    3. In the other three workflows, go to **Settings → Error workflow** and choose *HappyGut: email the team when a workflow fails*.

To stop n8n: `docker compose down`. Your workflows are kept in a Docker volume.

## Step 7: MCP servers (optional)
**In Claude Code:** open the repository. `.mcp.json` already lists `happygut-foodgraph`, `happygut-guidelines` and `happygut-evals`; approve them when Claude Code asks. Try "search the HappyGut rules about fat in a flare" or "what were HappyGut's evaluation results?".

**In Claude Desktop:** add the servers to `claude_desktop_config.json` (Settings → Developer → Edit config). Use your own path:
```json
{
  "mcpServers": {
    "happygut-guidelines": { "command": "uv", "args": ["run", "--project", "D:/Headshot/HappyGut/HappyGut/services/mcp", "happygut-guidelines"] },
    "happygut-evals": { "command": "uv", "args": ["run", "--project", "D:/Headshot/HappyGut/HappyGut/services/mcp", "happygut-evals"] }
  }
}
```

**The journal server** reads one patient's records with that patient's sign-in token.
1. With the backend running, get a token for a test account:
   ```powershell
   $body = @{ email = "rafi@happygut.test"; password = "<your TEST_PASSWORD_RAFI>" } | ConvertTo-Json
   (Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/v1/auth/login -ContentType "application/json" -Body $body).token
   ```
2. Add it to the Claude Desktop config:
   ```json
   "happygut-journal": {
     "command": "uv",
     "args": ["run", "--project", "D:/Headshot/HappyGut/HappyGut/services/mcp", "happygut-journal"],
     "env": { "HAPPYGUT_API_URL": "http://127.0.0.1:8000", "HAPPYGUT_PATIENT_TOKEN": "<the token>" }
   }
   ```
3. Restart Claude Desktop and ask "summarise this patient's last two weeks before a doctor's visit".

The token lasts 12 hours. Without `SESSION_SECRET` in `.env`, it also stops working whenever the backend restarts.

## Step 8: The flare model (nothing to do, unless you retrain)
The trained model ships in the repository (`services/api/src/happygut_api/models/`). To retrain it, for example after changing the simulator or the features, run this in `services\api` (about 2 minutes):
```powershell
uv run --extra ml python -m happygut_api.flare_model train
```
It rewrites the model, its card (`flare-risk-v1.json`) and `evals/FLARE_MODEL.md`. A test checks that the shipped model still beats the rule-based score; commit all three files together.

## Step 9: Run the tests
In `services\api`:
```powershell
uv run --group dev --extra pii pytest -q
```
Expect about 111 passing.

In `services\mcp`:
```powershell
uv run --group dev pytest -q
```
Expect 24 passing.

In `engine`:
```powershell
uv run --group dev pytest -q
```
Expect 99 passing.

In `apps\web`:
```powershell
npm run typecheck
```
```powershell
npm test
```

---

# Part C: Deployment (Hugging Face Space + Vercel)

The backend's Docker image (`services/api/Dockerfile`) now installs the tracing and ML extras, LightGBM's system library (`libgomp1`) and the red-flag suite used by the safety check. On the backend Space, set these **Secrets**:

| Secret | Value |
|---|---|
| `DEMO_MODE` | `true` |
| `TEST_PASSWORD_NUSRAT`, `TEST_PASSWORD_RAFI`, `TEST_PASSWORD_AYESHA` | Your throw-away passwords (the same ones you put in the portal) |
| `SESSION_SECRET` | A long random string |
| `GEMINI_API_KEY`, `GROQ_API_KEY` | Your keys |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` | From step 5 |
| `JOBS_TOKEN` | Same as in n8n |
| `CORS_ORIGINS` | `["https://<your-app>.vercel.app"]` |

**Watch the first build log.** The `libgomp1` install couldn't be tested here. If the model fails to load, the app still works and just shows the rule-based score.

**Vercel** (web app): root directory `apps/web`; environment variable `VITE_API_URL=https://<your-space>.hf.space`; and a `vercel.json` that rewrites every path to `/index.html`, so links like `/care` open directly (see `TEAM-HANDOVER.md` section 8).

**n8n in production:** run the image `n8nio/n8n:1.123.0` as a second Docker Space (set `app_port: 5678` in the Space's README header). Set `HAPPYGUT_API_URL` to the backend Space's URL and `N8N_ENCRYPTION_KEY` as secrets. Free Spaces lose files on restart, so point n8n's database at Supabase (`DB_TYPE=postgresdb` and the `DB_POSTGRESDB_*` variables). Then repeat step 6 there. The health workflow is what keeps the backend Space awake while judges test.

---

# Part D: Portal and video

- **Portal text:** paste the three sections of `docs/portal/submission-text.md` (v5.1).
- **Portal ticks:** follow `docs/portal/submission-scope.md`:
  - Tick **Langfuse** and **n8n** only once they actually run on the deployment.
  - Untick the research MCP server, Supabase webhooks and anything else marked **C**.
  - You can tick **four MCP servers built**, **LightGBM** and **workflow automation (n8n)** once n8n runs.
- **Video:** use script **v3** in `docs/portal/video-script.md` (19 Nov). It adds the **Add to diary** step, a live red-flag safety shot, the doctor's report and the ML flare model, and uses the 19 Nov numbers (109 dishes, 68%). Always say "simulated" with the 68% and the model's 2.7×.

---

# Part E: Troubleshooting

| Problem | Fix |
|---|---|
| No "Machine-learning estimate" on the card | The `ml` extra isn't installed: run step 3, and start the backend with the `--extra` flags (step 4) |
| `lib_lightgbm.dll` / `vcomp140.dll` error on Windows | Install the Microsoft Visual C++ Redistributable (x64), then run step 3 again |
| `/v1/health` shows `"tracing": false` | Both Langfuse keys must be set, the `tracing` extra installed, and the backend restarted |
| No traces in Langfuse | Check the region (EU vs US host), and wait a minute: traces are sent in batches |
| n8n nightly or safety check: 404 `jobs_disabled` | `JOBS_TOKEN` isn't set on the backend; add it and restart the backend |
| n8n: 401 `invalid_job_token` | The credential value must be `Bearer <JOBS_TOKEN>` exactly, with one space; check that the token matches `.env` |
| n8n can't reach the backend | Locally it must be `http://host.docker.internal:8000` and the backend must be running on the host |
| n8n: "Credential not found" | Open the HTTP node and select *HappyGut jobs token* (step 6.7) |
| Reminders don't appear | Allow notifications for the site in the browser; the app must be open or installed; dose reminders only fire within an hour of the dose time |
| Journal MCP: "sign-in has expired" | Get a new token (step 7); tokens last 12 hours and reset on restart without `SESSION_SECRET` |
| Weight, medicines or diary changes disappear | Expected in demo mode: records live in memory and reset when the backend restarts. Settings → "Restore original records" resets one account |

Questions: ask the team leader. If something here is out of date, fix it in a pull request.
