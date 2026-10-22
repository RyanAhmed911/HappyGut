# services/mcp: HappyGut MCP servers

All tools are read-only (`read_only_hint`), take validated inputs and return structured output. No server computes verdicts (the engine does), and only `happygut-journal` touches patient data (consent-scoped).

| Server | Tools | Status |
|---|---|---|
| `happygut-foodgraph` | `search_dish`, `get_components`, `explain_verdict_path` | ✅ built (MCP Python SDK v2, `MCPServer`) |
| `happygut-guidelines` | `search_guidelines`, `get_rule_card`, `cite_source` | planned (Step 4) |
| `happygut-evals` | `run_eval_suite`, `get_latest_metrics`, `compare_runs` | planned (Step 4) |
| `happygut-journal` | `get_symptom_trend`, `get_adherence`, `get_previsit_summary` | planned (Step 4) |
| `happygut-research` | `get_trigger_stats`, `list_cohorts` | planned (Step 4) |

## foodgraph
```bash
cd services/mcp
uv run --group dev pytest -q                                  # 13 tests (in-process MCP client)
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
