# services/mcp: HappyGut MCP servers

All tools are read-only (`read_only_hint`), take validated inputs and return structured output. No server computes verdicts (the engine does), and only `happygut-journal` touches patient data (consent-scoped).

| Server | Tools | Data | Status |
|---|---|---|---|
| `happygut-foodgraph` | `search_dish`, `get_components`, `explain_verdict_path` | Dishes, components, Rule Cards | ✅ built |
| `happygut-guidelines` | `search_rules`, `get_rule`, `list_sources` | The 25 approved Rule Cards with their papers and exact quotes | ✅ built (keyword search; no embeddings yet) |
| `happygut-evals` | `get_results`, `pattern_recovery`, `check_red_flags` | `evals/summary.json` and the red-flag sentinel | ✅ built |
| `happygut-journal` | `get_overview`, `get_recent_days`, `get_patterns` | ONE patient's records, read through the HappyGut API with that patient's own sign-in token | ✅ built |
| `happygut-research` | — | Consented, anonymised aggregates across patients | not built: there are no real patients to aggregate |

All servers run over stdio by default, or Streamable HTTP behind `MCP_BEARER_TOKEN` with `--http`:

```bash
cd services/mcp
uv run --group dev pytest -q                     # 24 tests (in-process MCP client)
uv run happygut-guidelines                       # stdio
uv run happygut-evals --http --port 8102         # HTTP (needs MCP_BEARER_TOKEN)
HAPPYGUT_API_URL=http://127.0.0.1:8000 HAPPYGUT_PATIENT_TOKEN=<the patient's token> uv run happygut-journal
```

**Journal consent.** The journal server can only read what the patient's own sign-in can read, and nothing it returns includes their name, free-text notes or photos. A patient (or a test account) shares it by giving the token to an AI client, for example a clinician's assistant before a visit; signing out or restoring the account ends it. It has no write tools.

## foodgraph
```bash
cd services/mcp
HAPPYGUT_INCLUDE_DRAFTS=1 uv run happygut-foodgraph            # stdio
MCP_BEARER_TOKEN=... uv run happygut-foodgraph --http --port 8100   # Streamable HTTP + bearer token
```
- Backend: `HAPPYGUT_GRAPH_BACKEND=memory` (default, built from approved seeds) or `neo4j` (reads Neo4j in read transactions; needs `NEO4J_*`).
- `HAPPYGUT_INCLUDE_DRAFTS=1` includes draft seeds for development; results show `status: draft`.
- Claude Code picks it up from `.mcp.json` in the repo root.

## Third-party MCP servers we use (configure locally; they need your keys)
- **Supabase MCP** in read-only mode, scoped to the project: see Supabase's MCP docs; never use it to change the schema (migrations do that)
- **Neo4j Cypher MCP** (`mcp-neo4j-cypher`): read tools only
- **GitHub MCP**, **Filesystem MCP** (limited to `data/`), **Playwright MCP** (test URLs only)
