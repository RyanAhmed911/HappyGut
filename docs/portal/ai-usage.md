# Portal text: AI detail usage (prototype, Oct 31)

> Paste-ready lists. Same rule as the data section: list only what's really used. Exact model versions are pinned after the Step 2 benchmark. Write the version names you actually run; don't copy placeholder names.

## Prompt usage

**Design**
- Prompts are versioned files in `prompts/runtime/` (id, version, model, temperature, output schema, last eval score)
- Every LLM call logs its prompt ID + version (Langfuse); every verdict stores the prompt version that explained it
- One prompt per agent task:
  - perception (photo → dishes)
  - dish resolver
  - evidence explainer
  - meal planner
  - red-flag checker
  - Rule Card extractor
  - contextual chunk header
  - evaluation judge
- Role prompting with hard boundaries: "clinical nutrition evidence explainer". Never says "safe", never diagnoses, never gives medication advice
- Structured outputs: every prompt returns JSON matching a Pydantic schema; invalid output is retried with the validation error fed back (Instructor)
- Few-shot: 3–5 curated examples per task (mixed Bangladeshi plate, Bangla label, Banglish text, blurry photo → ⚪ "Not sure")
- Grounded generation: the explainer only sees evidence objects with IDs, must cite an ID for every claim, and must say so when evidence is insufficient
- Quote-then-answer: extraction prompts copy the exact source sentence before producing a Rule Card (reduces hallucination)
- Minimal chain-of-thought: the verdict logic lives in the deterministic engine, so prompts don't need long reasoning. Faster and cheaper, with nothing hidden in model reasoning
- Bangla-first output: a medical-term glossary in the prompt keeps terminology consistent; plain language, ≤ 60 words, with an expandable "more"
- Layered safety: red-flag pre-check → guardrailed system prompt → post-output validator (bans "safe" and medication wording, checks every claim has a citation)

**Iteration and versioning**
- Eval-driven: every prompt change runs against the evaluation sets (promptfoo + Ragas) and is merged only if nothing regresses
- Failure cases found in testing become new few-shot examples or test cases
- Prompt versions compared side by side in Langfuse
- Build prompts (Claude Code sessions) kept in the prompt library `prompts/build/` with CLAUDE.md as project memory

## Token optimization

- Deterministic verdict engine: the decision needs no LLM, so a scan costs ~2 LLM calls (perception + explanation)
- LiteLLM router: cheap/fast model for routing and classification, stronger model only for vision and explanations; automatic fallback across providers when a free-tier quota runs out
- Caching: perception results by image SHA-256
- Caching: explanations by (dish, profile version, language); common dishes cost no new tokens
- Gemini implicit context caching: static prefix first (system prompt + glossary + few-shots), variable content last
- Compact evidence packets: top-5 reranked chunks reduced to short fact lines with IDs (~300 tokens) instead of raw documents
- Images downscaled to ≤ 1024 px before the vision model
- Local models (Ollama) handle high-volume, low-value work: PII scrubbing, Bangla normalisation, classification. Zero API tokens
- Batch jobs on the local GPU: Rule Card extraction, dish enrichment, contextual chunk headers are computed once at ingestion, never per query
- Semantic dedup: duplicate chunks removed by content hash before embedding
- Stateless calls, no chat history; weekly summaries are written from SQL-computed statistics, not raw logs
- Output caps: max_tokens per task, short answers with "more" on demand
- Streaming (SSE) for faster perceived response
- Token usage per call tracked in Langfuse

## Token optimization tools and methods (tick)
- ✅ Gemini Context Caching (implicit caching of the static prompt prefix)
- ✅ Structured outputs / JSON mode
- ✅ Cheap-model routing (LiteLLM)
- ✅ Request batching (offline enrichment and embedding jobs)
- ✅ Semantic chunk dedup
- ❌ Anthropic / OpenAI / DeepSeek caching (we don't call those APIs at runtime)
- ❌ LLMLingua, Graphify, Caveman, Codeburn, rolling summary, sliding window, KV-cache reuse, speculative decoding (not used)

## LLMs / models used (tick; +3 each, max 15)
- ✅ Claude
- ✅ Gemini
- ✅ Llama
- ✅ Qwen
- ✅ *Add:* Gemma
- ❌ ChatGPT, Kimi, DeepSeek, Mistral, Grok (not used; tick ChatGPT only if the team really uses it)

## How and why we use these LLMs
- Claude (via Claude Code): development only: architecture docs, code generation, refactoring, tests, reviews; project memory in CLAUDE.md. Not called at runtime (no free API tier)
- Gemini Flash (free tier): primary runtime model
  - meal/label photo → dishes JSON
  - Bangla/English evidence explanations
  - meal plans
  - weekly summaries
  - Why: strong vision + Bangla, JSON-schema output, free tier
- Llama (via Groq free tier): low-latency tasks
  - text-input intent routing
  - second check on red-flag free text
  - fallback explainer when the Gemini quota runs out
  - Why: very fast inference, separate quota
- Gemma (local, Ollama, ~12B quantized): privacy and local tasks
  - PII scrubbing (raw text never leaves our machine)
  - Bangla/Banglish normalisation
  - local vision fallback
  - Why: open weights, strong multilingual, fits 12 GB VRAM
- Qwen (local, Ollama, ~7–8B quantized): offline batch knowledge work
  - Rule Card extraction
  - dish enrichment
  - contextual chunk headers
  - synthetic Bangla/Banglish evaluation sets
  - LLM-as-judge (a different model family from the generator, to reduce self-bias)
  - Why: strong structured output, free unlimited batch runs
- Supporting (non-LLM) models: BGE-M3 multilingual embeddings, bge-reranker-v2-m3 cross-encoder
- Privacy note: free-tier cloud APIs may use submitted data to improve the provider's services, so only food photos and de-identified text are sent; production moves to paid tiers with no-training terms

## Retrieval & RAG (tick)
- ✅ Contextual RAG (Anthropic-style context per chunk)
- ✅ Variable / Semantic Chunking
- ✅ Graph RAG
- ✅ Knowledge Graph / Other Graph Methods
- ✅ Hybrid Search (Keyword + Vector)
- ✅ Rerankers (BGE)
- ➖ True but not ticked (no extra points): Naive RAG, Vector Database (pgvector), Query Rewriting
- ❌ Late Chunking, Agentic RAG, Self-RAG, Corrective RAG, HyDE (not used as named techniques)

## RAG architecture details
**Two retrieval paths, fused into one evidence packet**

Graph path (food facts and personal history)
- Dish resolution: Banglish → Bangla → canonical dish ID (pg_trgm + BGE-M3 name embeddings)
- Neo4j traversal: Dish → Ingredient → Component (level per 100 g)
- Rule Cards matching (component, phenotype, disease state) → cited Papers
- Patient REACTS_TO edges (personal evidence) + GENTLER_ALTERNATIVE dishes

Text path (guideline passages for the explanation)
- Corpus: CC-licensed ESPEN / IOIBD / AGA guideline text, published FODMAP composition papers, Rule Card texts
- Parsing: Docling, structure-aware (sections, headings; tables kept whole)
- Variable chunking: split by section first, then semantic breakpoints (embedding-similarity drops) into ~200–500-token chunks
- Contextual RAG: local Qwen writes a 50–100-token context header per chunk (document, section, population, recommendation strength), prepended before embedding and keyword indexing; generated once at ingestion
- Embeddings: BGE-M3, 1024-d, multilingual (Bangla queries match English guidelines)
- Index: pgvector HNSW (cosine, m=16, ef_construction=64)
- Keyword search: Postgres tsvector (English) + pg_trgm (Bangla/Banglish)
- Metadata filters: licence, phenotype, disease state, document type
- Query: built from structured facts (component + phenotype + state), not raw user text
- Hybrid fusion: Reciprocal Rank Fusion, top 50 → bge-reranker-v2-m3 → top 5

Evidence gate and grounding
- Low reranker score or no matching Rule Card → no explanation from weak evidence → ⚪ "Not sure" + a clarifying question
- Evidence packet = IDs + short fact lines (~300 tokens) → the explainer must cite IDs → a validator checks every cited ID was in the packet

Evaluation
- Recall@5, MRR on the guideline Q&A set
- Ragas faithfulness and context precision
- Ablation table: naive vector → + contextual headers → + hybrid → + reranker

## MCP usage
> **Status: PLANNED.** Fill in the portal only for servers that run by Oct 31. Repo/deploy URLs and "# endpoints actually called" come from the real build.

### Built
**happygut-foodgraph** · tick "Reused across multiple projects / clients"
- # tools: 3
- Transport: stdio, Streamable HTTP
- Language / SDK: Python, MCP Python SDK (FastMCP)
- Repo / deploy URL: GitHub repo path `mcp/foodgraph` + Cloudflare Tunnel URL *(after build)*
- Purpose: exposes the HappyGut Food Knowledge Graph (Bangladeshi dishes → ingredients → gut-relevant components → cited IBD Rule Cards) as read-only tools, so the app's agent, our dev tools and clinicians' AI clients share one trusted source of food evidence instead of duplicating graph queries. No patient data.
- Tools:
  - `search_dish(query, lang)`: Bangla/English/Banglish name → canonical dishes
  - `get_components(dish_id)`: ingredients, component levels, sources
  - `explain_verdict_path(dish_id, phenotype, state)`: graph path dish → component → Rule Card → paper

**happygut-journal** *(only if built by Oct 31)* · tick reuse
- # tools: 3
- Transport: Streamable HTTP
- Language / SDK: Python, FastMCP
- Purpose: lets a clinician's AI client read one patient's consented, read-only summary before a visit; bearer token per clinician, scoped to patients who shared via QR
- Tools:
  - `get_symptom_trend(patient_ref, days)`
  - `get_adherence(patient_ref, days)`
  - `get_previsit_summary(patient_ref)`

### Used
**Supabase MCP**
- Source: Supabase (official)
- # endpoints called: ~4
- Capabilities: tools `list_tables`, `apply_migration`, `execute_sql`, `generate_typescript_types`
- How: Claude Code designed and applied the Postgres schema and migrations, checked row-level security policies, and generated TypeScript types

**Neo4j Cypher MCP** (`mcp-neo4j-cypher`)
- Source: Neo4j Labs (open source)
- # endpoints called: 3
- Capabilities: tools `get_neo4j_schema`, `read_neo4j_cypher`, `write_neo4j_cypher`
- How: Claude Code inspected the graph schema, found orphan nodes and unmatched ingredients, and proposed fixes that we reviewed

**Filesystem MCP**
- Source: Model Context Protocol reference servers (open source)
- # endpoints called: ~3
- Capabilities: tools `list_directory`, `read_text_file`, `search_files`
- How: Claude Code browsed raw/bronze data-lake folders during parser and ingestion work

### MCP clients / hosts
- Claude Code: development, schema work, graph curation
- HappyGut meal-check agent: LangGraph via `langchain-mcp-adapters` → `happygut-foodgraph`
- Claude Desktop: demo of exploring the food graph / clinician summary

### Transports
- ✅ stdio
- ✅ Streamable HTTP
- ❌ SSE (legacy), WebSocket

### Reuse, architecture and integration notes
- One foodgraph server serves the app agent, Claude Code curation and the Claude Desktop demo, so there's a single source of graph logic
- All built tools are read-only; writes go only through the reviewed ingestion pipeline
- Data separation: food knowledge (foodgraph) vs consented patient data (journal); research gets aggregates only
- Auth: bearer tokens on Streamable HTTP, published through Cloudflare Tunnel with Access service tokens; stdio local only
- Rate limits: per-token limits in the server + Cloudflare WAF rule
- Observability: every tool call traced in Langfuse (tool, latency, caller)
- Typed contracts: Pydantic input/output models generate the tool JSON schemas

### Anything else about MCP
- Design choice: MCP for knowledge access, but the verdict engine itself stays in-process (deterministic, unit-tested), so the same decision logic isn't spread across tools
- Gotcha planned for: free-tier tunnel URLs change, so a named Cloudflare Tunnel keeps a stable endpoint for clients
- Next: `happygut-research` (aggregated, privacy-protected trigger statistics for researchers), plus MCP resources for Rule Cards and the prompt library
