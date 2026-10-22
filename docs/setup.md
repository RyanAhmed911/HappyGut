# Setup (Step 0): accounts and development

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
| 8 | ngrok | Free account; claim the free static domain | — |
| 9 | api.data.gov, NCBI | Free API keys | `USDA_API_KEY`, `NCBI_API_KEY` |

Generate random secrets for `MCP_BEARER_TOKEN` and `N8N_ENCRYPTION_KEY`, e.g. `python -c "import secrets;print(secrets.token_urlsafe(32))"`.

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

### ngrok and data API keys
- **ngrok**: on "Where do you want to begin?" choose **Share localhost**, and claim the free static domain under **Domains**. Skip "Gateway" and "AI Gateway".
- **USDA FoodData Central key**: https://api.data.gov/signup/ (the same key works for FoodData Central) → `USDA_API_KEY`
- **NCBI key**: sign in at https://www.ncbi.nlm.nih.gov/account/ → Account Settings (https://account.ncbi.nlm.nih.gov/settings/) → API Key Management → Create → `NCBI_API_KEY`

### Until the repo is cloned
Keep every key in a password manager or private note (not chat, email or GitHub). On the first clone, copy `.env.example` to `.env` and paste them in.

## 2. Development on Windows
**Treat the project as having no local GPU.** The live app runs entirely on free cloud services (Hugging Face Spaces, Supabase, Neo4j, Gemini, Groq), and all development happens on Windows.

**1. Tools** (PowerShell)
```powershell
winget install Git.Git GitHub.cli OpenJS.NodeJS.LTS Microsoft.VisualStudioCode ngrok.ngrok
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"   # Python tooling
```
Close and reopen PowerShell afterwards.

**2. Get the code** (after PR #9 is merged)
```powershell
gh auth login                     # GitHub.com → HTTPS → login with a web browser
gh repo clone RyanAhmed911/HappyGut
cd HappyGut
```

**3. Secrets**
```powershell
Copy-Item .env.example .env
python -c "import secrets;print(secrets.token_urlsafe(32))"   # run twice: MCP_BEARER_TOKEN, N8N_ENCRYPTION_KEY
code .env                         # paste every key, save
```

**4. ngrok**
```powershell
ngrok config add-authtoken <your-token>     # dashboard → Your Authtoken
```

**5. Tests**
```powershell
cd engine; uv run --group dev pytest -q; cd ..
cd pipelines; uv run python -m happygut_pipelines.seeds; uv run --group dev pytest -q; cd ..
```
Expected: 62 passed and 9 passed, and the validator prints `OK`.

Docker Desktop is optional: install it only if you want to run n8n locally (`docker compose up -d`). Production n8n runs on Hugging Face Spaces.

## 3. Ubuntu: GPU jobs (finite, started by hand)
Ubuntu is used only for GPU jobs that you start and that finish on their own. It is never a server, and it needs **no `.env`**: each job reads its inputs from the repo and commits its outputs back as versioned files, which Windows then loads into Supabase / Neo4j.

| Job | Model / runtime | Output | When |
|---|---|---|---|
| G1 Contextual headers | Qwen 2.5 7B (Ollama) | headers for every guideline chunk | Step 1 |
| G2 Bangla aliases | Gemma 3 4B (Ollama) | Bangla/Banglish name variants for dishes (reviewed before use) | Step 1 |
| G3 Corpus embeddings | BGE-M3 (ROCm PyTorch) | vectors for chunks, Rule Cards, dish names | Step 1 |
| G4 Test utterances | Llama 3.2 3B (Ollama) | synthetic Bangla/Banglish/English test inputs (reviewed) | Step 4 |
| G5 Evaluation judge | DeepSeek-R1-Distill 7B (Ollama) | judge scores for the evaluation run | Step 4 |
| G6 Dish-name fine-tune | BGE-M3 + sentence-transformers (ROCm PyTorch) | fine-tuned encoder pushed to Hugging Face | Step 4 |

Docker isn't needed on Ubuntu; you can leave it installed or remove it.

### One-time preparation (~30 minutes plus model downloads)
**1. Ollama settings**
```bash
sudo systemctl edit ollama
```
Add these lines in the empty part at the top, then save and close:
```
[Service]
Environment="OLLAMA_MAX_LOADED_MODELS=3"
Environment="OLLAMA_KEEP_ALIVE=30m"
```
```bash
sudo systemctl restart ollama
ss -ltnp | grep 11434             # must show 127.0.0.1:11434 (not 0.0.0.0)
```
- `systemctl edit` saves an override file that adds settings to the Ollama background service.
- `OLLAMA_MAX_LOADED_MODELS=3`: up to 3 models in GPU memory at once (also Ollama's default for one GPU).
- `OLLAMA_KEEP_ALIVE=30m`: models load only when a job uses them and unload 30 minutes after their last use (default 5 minutes). With no job running, Ollama uses no VRAM; `ollama stop <model>` frees it immediately.
- The `ss` check confirms Ollama only listens on this computer.

**2. Models** (~17 GB download; can run while you do something else)
```bash
ollama pull qwen2.5:7b
ollama pull gemma3:4b
ollama pull llama3.2:3b
ollama pull deepseek-r1:7b
ollama run gemma3:4b "Say hello in Bangla" && ollama ps    # PROCESSOR should say 100% GPU
```

**3. Check ROCm PyTorch** (used by G3 and G6)
```bash
python3 -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```
It should print your torch version, `True` and the Radeon GPU's name. (ROCm builds of PyTorch use the `cuda` names.)

**4. Tools and code (no secrets)**
```bash
sudo apt install -y git gh
curl -LsSf https://astral.sh/uv/install.sh | sh    # then open a new terminal
gh auth login                                      # GitHub.com → HTTPS → web browser
gh repo clone RyanAhmed911/HappyGut
```

### Running a job (when Claude says it's ready)
```bash
cd HappyGut && git pull
# run the command Claude gives you, e.g. uv run python -m happygut_pipelines.gpu_jobs g1
git add data/gpu_jobs && git commit -m "GPU job G1 outputs" && git push
```
Then boot back into Windows, `git pull`, and load the outputs.

## 4. Start collecting meal photos today
Target ~300 photos of real Bangladeshi meals (home, restaurant, street food), 30–50 a day across the team. **Food only, no people.** Save as `data/raw/photos/<dish-id>/<n>.jpg` (this folder is gitignored) and keep a simple CSV of `file, dish_ids, taken_by`.
