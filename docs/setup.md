# Setup (Step 0): accounts and the GPU machine

All free tiers, **no card needed anywhere**. Put every key in `.env` (copy `.env.example`). Never commit `.env`.

## 1. Accounts (one person each, share keys privately)
| # | Service | What to do | `.env` keys |
|---|---|---|---|
| 1 | Supabase | See **Supabase project settings** below | `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `SUPABASE_DB_URL` |
| 2 | Neo4j AuraDB Free | Create a free instance; save the generated password (shown once) | `NEO4J_URI`, `NEO4J_PASSWORD` |
| 3 | Google AI Studio | aistudio.google.com → Get API key. **Not** Google Cloud / Vertex | `GEMINI_API_KEY` |
| 4 | Groq | console.groq.com → API key | `GROQ_API_KEY` |
| 5 | Langfuse Cloud | Hobby plan → new project → API keys | `LANGFUSE_*` |
| 6 | Vercel | Hobby account, connect GitHub | — |
| 7 | Hugging Face | Account (for Spaces + model downloads) | — |
| 8 | Tailscale | Personal plan; install on the GPU machine; enable **Funnel** in the admin console | `GPU_GATEWAY_URL` |
| 9 | ngrok | Free account; claim the free static domain | — |
| 10 | api.data.gov, NCBI | Free API keys | `USDA_API_KEY`, `NCBI_API_KEY` |

Generate random secrets for `GATEWAY_KEY`, `MCP_BEARER_TOKEN` and `N8N_ENCRYPTION_KEY`, e.g. `python -c "import secrets;print(secrets.token_urlsafe(32))"`.

### Supabase project settings
| Setting | Choose | Why |
|---|---|---|
| Name | `happygut` | One project for build and demo. Keep the second free slot as a spare. Safety comes from read-only MCP, reviewed migrations and simulated-only data instead of a second project |
| Database password | **Generate**, save it in a password manager | It goes into `SUPABASE_DB_URL` in `.env` only |
| Region | The most specific Asia-Pacific option available, ideally **Mumbai** (South Asia), else **Singapore** | Closest to Bangladesh (lower latency) |
| Enable Data API | **On** | The app uses `supabase-js` for auth, realtime and reading its own history |
| Automatically expose new tables | **Off** | Nothing becomes reachable through the API by accident; migrations grant access table by table |
| Enable automatic RLS | **On** | Every new table starts locked; migrations add per-patient policies (Constitution V) |
| Postgres type | **Default** | OrioleDB is an experimental storage engine; we need standard extensions (`vector`, `pg_trgm`, `pg_cron`) |

After the project is created:
1. Database → Extensions: enable `vector`, `pg_trgm`, `pg_cron`.
2. **Keys** (Project Settings → API Keys): copy the **publishable key** (`sb_publishable_…`) into `SUPABASE_PUBLISHABLE_KEY`, and the **secret key** (`sb_secret_…`, click to reveal) into `SUPABASE_SECRET_KEY`. The secret key is for the backend only.
3. **Project URL**: it isn't on the API Keys page. Find it in any of these places:
   - Project Settings → **Data API**, at the top as "Project URL"
   - the green **Connect** button → **App Frameworks** tab, shown as `SUPABASE_URL`
   - or build it yourself: Project Settings → General → **Project ID**, then `https://<project-id>.supabase.co`

   Put it in `SUPABASE_URL`.
4. **Database connection string** (green **Connect** button at the top of the project page):
   - This is the database's address plus login, which the Python backend uses to talk to Postgres directly.
   - In the **Connection String** tab, choose type **URI**, then look for **Session pooler**. Don't pick "Direct connection": on the free plan it only works on IPv6 networks, which most home internet and hosting services aren't.
   - Copy it. It looks like `postgresql://postgres.<project-id>:[YOUR-PASSWORD]@aws-0-<region>.pooler.supabase.com:5432/postgres`
   - Replace `[YOUR-PASSWORD]`, brackets included, with the database password you saved when creating the project.
   - If the password contains `@ : / # ? %`, either reset it (Project Settings → Database) to letters and numbers only, or URL-encode those characters.
   - Paste the result into `SUPABASE_DB_URL`.
5. Free projects pause after about a week without activity; open the dashboard or run a query before demos.

## 2. GPU machine
Requirements: NVIDIA GPU (12 GB), Docker with GPU support (Windows: Docker Desktop + WSL2; Linux: nvidia-container-toolkit), Tailscale.

```bash
# from the repo root, with .env filled in
docker compose up -d                      # ollama, gateway, n8n

# pull the local models (Q4 quantized by default)
docker compose exec ollama ollama pull gemma3:4b
docker compose exec ollama ollama pull llama3.2:3b
docker compose exec ollama ollama pull qwen2.5:7b
docker compose exec ollama ollama pull deepseek-r1:7b

# check the gateway locally
curl http://127.0.0.1:8080/health                                       # ok
curl -H "X-HappyGut-Key: $GATEWAY_KEY" http://127.0.0.1:8080/llm/api/tags   # model list

# publish the gateway (stable https://<machine>.<tailnet>.ts.net)
tailscale funnel --bg 8080
```

**Bangla smoke test (10 minutes):** ask `gemma3:4b` to (1) rewrite a Banglish sentence in Bangla, (2) remove the name and phone number from a Bangla sentence, (3) list the dishes in a photo of a Bangladeshi meal. Note the quality in `docs/02-architecture.md` so we can pin the model.

## 3. Start collecting meal photos today
Target ~300 photos of real Bangladeshi meals (home, restaurant, street food), 30–50 a day across the team. **Food only, no people.** Save as `data/raw/photos/<dish-id>/<n>.jpg` (this folder is gitignored) and keep a simple CSV of `file, dish_ids, taken_by`.
