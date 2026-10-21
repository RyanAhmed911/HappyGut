# Step 2: Architecture and stack

> Status: **v1.0** (2026-10-21). Scope is the preliminary prototype (tiers A and B in `docs/portal/submission-scope.md`). Rules: `.specify/memory/constitution.md`.

## 1. System overview

```mermaid
flowchart LR
    subgraph Phone["📱 Patient phone"]
        PWA["React + Vite PWA<br/>(Vercel)"]
    end
    subgraph HF["Hugging Face Spaces (free CPU)"]
        API["FastAPI /v1<br/>LangGraph meal-check graph<br/>verdict engine"]
    end
    subgraph Cloud["Free cloud services"]
        SB[("Supabase<br/>Postgres + pgvector<br/>Auth · Storage · Realtime")]
        NEO[("Neo4j AuraDB Free<br/>Food KG + Personal Gut Graph")]
        GEM["Gemini (AI Studio)<br/>vision + explanation"]
        GROQ["Groq Llama<br/>routing · fallback"]
        LF["Langfuse<br/>traces · scores"]
    end
    subgraph GPU["Team GPU machine (12 GB) · Docker Compose"]
        GW["Caddy API-key gateway"]
        OLL["Ollama<br/>Gemma 3 4B · Llama 3.2 3B<br/>Qwen 2.5 7B · R1-Distill 7B"]
        EMB["Embed + rerank service<br/>BGE-M3 · bge-reranker-v2-m3"]
        MCP["MCP servers<br/>foodgraph · guidelines · journal · evals · research"]
        N8N["n8n"]
        PIPE["Knowledge pipelines<br/>(batch)"]
    end
    PWA -- HTTPS + Supabase JWT --> API
    PWA -- auth · realtime --> SB
    API --> SB
    API --> NEO
    API --> GEM
    API --> GROQ
    API -- "Tailscale Funnel" --> GW
    GW --> OLL
    GW --> EMB
    GW --> MCP
    API --> LF
    N8N --> API
    PIPE --> SB
    PIPE --> NEO
```

## 2. Meal-check request flow (the hero flow)

```mermaid
sequenceDiagram
    participant U as PWA
    participant A as FastAPI (LangGraph)
    participant L as Local (Gemma, embed)
    participant G as Gemini
    participant K as Neo4j + pgvector
    participant E as Verdict engine
    U->>A: POST /v1/meal-checks (photo or text, lang)
    A->>A: Safety Sentinel (red-flag rules) → stop + escalate if triggered
    A->>L: PII scrub (text only)
    A->>G: Perception: photo → dishes, ingredients, method, portion, confidence
    A-->>U: SSE: dishes found
    A->>K: Resolve dishes (trigram + embeddings) → components → Rule Cards → papers
    A->>K: Hybrid RAG (guideline chunks, rerank) + personal REACTS_TO edges
    A->>E: evidence + profile (phenotype, state)
    E-->>A: verdict per dish + overall, scores, evidence IDs, confidence
    A-->>U: SSE: verdict
    A->>G: Explain (evidence packet only, cite IDs, bn/en)
    A->>A: Output guard (schema, citations ⊆ evidence, verdict match, banned words)
    A-->>U: SSE: explanation + alternative
    A->>K: Store meal_check (evidence IDs, model + prompt versions)
```

If the GPU machine is unreachable, PII scrubbing falls back to Presidio-only rules, embeddings fall back to keyword + trigram search, and the UI shows a degraded-mode banner.

## 3. Verdict engine (`engine/`, pure Python, no network)

**Inputs**
- Resolved dishes, each with components and levels (`none`, `low`, `medium`, `high`)
- Applicable Rule Cards: (component, phenotype, disease state) → severity 0–3, `hard` flag, citation
- Personal posteriors per component: P(trigger), credible interval, number of exposures
- Profile: diagnosis (CD / UC), phenotype (incl. stricturing), state (remission / flare)
- Confidences from perception and dish resolution

**Algorithm (v0)**
1. Hard rules first. A `hard` Rule Card match (e.g. stricturing + insoluble fibre ≥ medium) → 🔴, and the reason is fixed.
2. Guideline score per component = severity × level weight (low 0.33, medium 0.66, high 1.0) × state multiplier (flare 1.3, remission 1.0).
3. Personal score per component = P(trigger) when exposures ≥ 3; otherwise the prior is used, at reduced weight.
4. Component risk = max(guideline score / 3, personal score). Dish risk = max over its components. Meal = max over dishes.
5. Thresholds: < 0.35 🟢 · 0.35–0.65 🟡 · > 0.65 🔴.
6. Confidence = min(perception confidence, resolution confidence, evidence coverage). Below 0.5 → ⚪ "Not sure" plus a clarifying question.
7. Output: verdict, per-component contributions (for the evidence bar), evidence IDs, and the gentler alternative (lowest-risk `GENTLER_ALTERNATIVE` dish).

All weights and thresholds live in one versioned config file. Every branch has a unit test.

## 4. Repository layout

```
apps/web/            React + Vite PWA (Lovable syncs here)
services/api/        FastAPI app, LangGraph graph, Pydantic-AI agent nodes
services/mcp/        FastMCP servers: foodgraph, guidelines, journal, evals, research
services/gateway/    Caddyfile for the API-key gateway on the GPU machine
engine/              Verdict engine + Trigger Discovery (pure Python, unit-tested)
pipelines/           Knowledge build: crawl → parse → resolve → enrich → load
evals/               Test sets, promptfoo config, Ragas runs, Streamlit Eval Lab
prompts/runtime/     Versioned runtime prompts (id, version, model, schema)
data/                Raw / bronze files (gitignored), seeds (committed)
specs/               Spec-Kit feature specs (spec, plan, tasks)
docs/                Strategy, data, architecture, portal texts
docker-compose.yml   GPU machine services
```

## 5. Interfaces
- REST `/v1` (OpenAPI):
  - `POST /meal-checks` (SSE)
  - `GET /meal-checks/{id}`
  - `POST /meal-checks/{id}/feedback`
  - `POST /checkins`
  - `GET /insights/triggers`
  - `GET /insights/flare-risk`
  - `POST /reports/previsit`
  - `GET /foods/search`
  - `GET /health`
- Auth: Supabase JWT verified in FastAPI; row-level security in Postgres as a second line.
- MCP: read-only tools only; Streamable HTTP routes go through the gateway with an API key + bearer token.

## 6. Decision log

| # | Decision | Why | Alternatives rejected |
|---|---|---|---|
| AR1 | React + Vite PWA, not Next.js | Lovable generates React + Vite; no server rendering needed | Next.js (adds a server, doesn't match Lovable) |
| AR2 | FastAPI in Docker on Hugging Face Spaces | Free with no card, sleeps only after long idle; keeps the app up when the GPU machine is off | Render (slow cold starts), the GPU machine (single point of failure), Google Cloud Run (needs a card) |
| AR3 | GPU services via Tailscale Funnel behind a Caddy API-key gateway | Free, no card, stable `*.ts.net` address; Ollama has no built-in auth | Cloudflare named tunnel (needs a paid domain), quick tunnels (URL changes on restart) |
| AR4 | Deterministic verdict engine as a separate package | Safety, testability, explainability (Constitution III) | LLM-decided verdicts |
| AR5 | LangGraph + Pydantic-AI | Graph control flow + typed agent nodes; one interface to Gemini, Groq and Ollama | CrewAI / AutoGen as the main orchestrator |
| AR6 | LiteLLM router with cross-provider fallback | Free-tier quotas run out; routing keeps the demo alive | Single provider |
| AR7 | Supabase for Postgres, vectors, auth, storage, realtime | One free service instead of five | Separate vector DB, auth provider, object store |
| AR8 | Neo4j AuraDB Free for the knowledge graph | Graph RAG and the Personal Gut Graph need real graph traversal | Recursive SQL over tables |
| AR9 | ~50 dishes and ~25 Rule Cards for the prototype | 10 days left; depth and correctness beat breadth | 150 dishes |
| AR10 | Degraded mode when the GPU machine is offline | The demo must survive the team machine being off | No fallback |
