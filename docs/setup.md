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

### Neo4j AuraDB Free
1. Go to console.neo4j.io and sign up (Google or email; no card).
2. **Create instance** → choose **AuraDB Free**. Name it `happygut`. If a region choice is offered, pick the closest Asia option; otherwise keep the default.
3. A credentials screen appears **once**. Click **Download and continue** to save the `.txt` file. It contains `NEO4J_URI` (`neo4j+s://<id>.databases.neo4j.io`), `NEO4J_USERNAME` (`neo4j`) and `NEO4J_PASSWORD`. Store it with your other secrets.
4. Wait until the instance status says **Running** (a few minutes).
5. Skip optional extras (agents, graph analytics, sample datasets).
6. Free instances pause when unused for a few days. Resume them from the console before working or demoing.

### Tailscale, ngrok and data API keys
- **Tailscale**: install on **Ubuntu** (the GPU machine), not Windows. Funnel publishes the machine that runs the services. Install it on Windows only if you want to reach the Ubuntu box from there.
  `curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up`, then enable Funnel for the tailnet in the admin console.
- **ngrok**: on "Where do you want to begin?" choose **Share localhost**. Later on Ubuntu: install the agent, run `ngrok config add-authtoken <token>`, and claim the free static domain under **Domains**. Skip "Gateway" and "AI Gateway".
- **USDA FoodData Central key**: https://api.data.gov/signup/ (the same key works for FoodData Central) → `USDA_API_KEY`
- **NCBI key**: sign in at https://www.ncbi.nlm.nih.gov/account/ → Account Settings (https://account.ncbi.nlm.nih.gov/settings/) → API Key Management → Create → `NCBI_API_KEY`

### Until the repo is cloned
Keep every key in a password manager or private note (not chat, email or GitHub). On the first clone, copy `.env.example` to `.env` and paste them in.

## 2. GPU machine (Ubuntu, AMD RX 7700 XT): step by step
Already installed: ROCm, ROCm PyTorch, Ollama (native), llama.cpp. The machine dual-boots, so **the local AI only works while it's booted into Ubuntu**; keep it on Ubuntu during demo and judging windows.

| Runs natively on Ubuntu | Runs in Docker |
|---|---|
| Ollama (ROCm), rerank service (ROCm PyTorch, from Step 1) | Caddy API-key gateway, n8n |

**1. Check what's there**
```bash
rocminfo | grep -m1 gfx          # should show gfx1101 (RX 7700 XT)
ollama --version
systemctl status ollama --no-pager | head -3
df -h ~                          # need ~25 GB free for the models
```

**2. Basic tools**
```bash
sudo apt update && sudo apt install -y git curl gh
curl -LsSf https://astral.sh/uv/install.sh | sh     # Python tooling; open a new terminal afterwards
```

**3. Docker Engine**
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# log out and back in, then:
docker run --rm hello-world
```

**4. Get the code** (after PR #9 is merged)
```bash
gh auth login                     # GitHub.com → HTTPS → login with a web browser
gh repo clone RyanAhmed911/HappyGut
cd HappyGut
```

**5. Secrets**
```bash
cp .env.example .env
python3 -c "import secrets;print(secrets.token_urlsafe(32))"   # run 3 times: GATEWAY_KEY, MCP_BEARER_TOKEN, N8N_ENCRYPTION_KEY
nano .env                         # paste every key; save with Ctrl+O, Enter, exit with Ctrl+X
chmod 600 .env
```
Leave `GPU_GATEWAY_URL` empty until step 9.

**6. Ollama settings**
```bash
sudo systemctl edit ollama
```
In the editor, add these lines in the empty part at the top, then save and close:
```
[Service]
Environment="OLLAMA_MAX_LOADED_MODELS=3"
Environment="OLLAMA_KEEP_ALIVE=24h"
```
```bash
sudo systemctl restart ollama
ss -ltnp | grep 11434             # must show 127.0.0.1:11434 (not 0.0.0.0)
```
What this does: `systemctl edit` saves an override file (`/etc/systemd/system/ollama.service.d/override.conf`) that adds settings to the Ollama background service.
- `OLLAMA_MAX_LOADED_MODELS=3`: up to 3 models can sit in GPU memory at once (Gemma, Llama, BGE-M3). This is already Ollama's default for one GPU; it's written down so the setup is explicit.
- `OLLAMA_KEEP_ALIVE=24h`: a model stays loaded for 24 h after its last use instead of the default 5 minutes. Without it, the first scan after a quiet period waits several seconds while the model reloads. The cost is that the VRAM stays occupied; free it with `ollama stop <model>`.

The `ss` check confirms Ollama only listens on this computer, so the gateway is the only way in.

**7. Models** (~17 GB download)
```bash
ollama pull gemma3:4b
ollama pull llama3.2:3b
ollama pull qwen2.5:7b
ollama pull deepseek-r1:7b
ollama pull bge-m3
ollama run gemma3:4b "Say hello in Bangla"
ollama ps                         # PROCESSOR column should say 100% GPU
```

**8. Gateway + n8n**
```bash
docker compose up -d
docker compose ps
curl http://127.0.0.1:8080/health                                         # ok
KEY=$(grep '^GATEWAY_KEY=' .env | cut -d= -f2)
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/llm/api/tags    # 401 (no key)
curl -s -H "X-HappyGut-Key: $KEY" http://127.0.0.1:8080/llm/api/tags | head -c 300   # model list
```

**9. Tailscale Funnel**
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up                 # open the printed link and log in
sudo tailscale funnel --bg 8080   # first time: follow the printed link to enable Funnel, then rerun
tailscale funnel status           # shows https://<machine>.<tailnet>.ts.net
```
Put that https address into `GPU_GATEWAY_URL` in `.env`. From your phone (mobile data), open `https://<machine>.<tailnet>.ts.net/health`; it should say `ok`. The first visit can take a minute while the certificate is issued.

**10. ngrok agent** (used later for webhooks)
```bash
sudo snap install ngrok
ngrok config add-authtoken <your-token>     # dashboard → Your Authtoken
```

**11. Tests**
```bash
cd engine && uv run --group dev pytest -q && cd ..
cd pipelines && uv run python -m happygut_pipelines.seeds && uv run --group dev pytest -q && cd ..
```

**Bangla smoke test (10 minutes):** ask `gemma3:4b` to (1) rewrite a Banglish sentence in Bangla, (2) remove the name and phone number from a Bangla sentence, (3) list the dishes in a photo of a Bangladeshi meal. Note the quality in `docs/02-architecture.md` so we can pin the model.

## 3. Start collecting meal photos today
Target ~300 photos of real Bangladeshi meals (home, restaurant, street food), 30–50 a day across the team. **Food only, no people.** Save as `data/raw/photos/<dish-id>/<n>.jpg` (this folder is gitignored) and keep a simple CSV of `file, dish_ids, taken_by`.
