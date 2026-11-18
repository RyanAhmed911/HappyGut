# n8n workflows

Four workflows that run HappyGut's scheduled work. They only call the backend's API; secrets live in n8n
credentials, never in these files. A test (`services/api/tests/test_n8n_workflows.py`) checks that each
file is well-formed, calls a route that exists and holds no secret.

| Workflow | When | What it does |
|---|---|---|
| `happygut-health.json` | every 30 minutes | Calls `/v1/health`. Keeps the Hugging Face Space awake for judges (free Spaces sleep after ~48 h without traffic) and fails the run if the knowledge layer isn't fully loaded and reviewed |
| `happygut-nightly.json` | 23:30 Asia/Dhaka | Calls `POST /v1/jobs/nightly`: refreshes every patient's insights for the new day and records aggregate counts (patients, diaries filled, in a flare, high flare risk, weight notices, doses ticked). No names or records |
| `happygut-safety-check.json` | Mondays 07:10 | Calls `POST /v1/jobs/selfcheck`: runs the red-flag suite, verdict reproducibility, the stricture rule and the dish-name index on the live backend, and fails the run if any check fails |
| `happygut-alert.json` | when another workflow fails | Optional. Emails the team. Set it as the **Error Workflow** in the other three workflows' settings; needs an SMTP credential |

Each scheduled workflow also has a **Run now** trigger for testing.

## Set up locally (Docker)
1. In the repo-root `.env`: `N8N_ENCRYPTION_KEY` (any long random string), `JOBS_TOKEN` (at least 24 characters) and, optionally, `HAPPYGUT_ALERT_FROM` / `HAPPYGUT_ALERT_TO`.
2. Start the backend on the host (`uv run uvicorn --factory happygut_api.main:app --port 8000` in `services/api`) and n8n: `docker compose up -d`.
3. Import the workflows: `docker compose exec n8n n8n import:workflow --separate --input=/workflows`.
4. Open http://localhost:5678, create the credential **HappyGut jobs token** (type *Header Auth*): Name `Authorization`, Value `Bearer <JOBS_TOKEN>`. For alerts, create **HappyGut alert email** (type *SMTP*).
5. Open each workflow, pick the credential if n8n asks, press **Test workflow**, then switch it **Active**.

## Production
Run the same image (`n8nio/n8n:1.123.0`) as a Docker Hugging Face Space (port 5678), with `HAPPYGUT_API_URL` set to the backend Space's URL, the same `JOBS_TOKEN` on the backend Space, and `N8N_ENCRYPTION_KEY` as Space secrets. Free Spaces don't keep files across restarts, so point n8n's database at Supabase Postgres (`DB_TYPE=postgresdb` and the `DB_POSTGRESDB_*` variables) to keep workflows and credentials.
