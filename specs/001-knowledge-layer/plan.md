# Implementation Plan: Knowledge layer

**Branch**: `001-knowledge-layer` (worked on `claude/compassionate-cori-rd8y6n`) · **Date**: 2026-10-22 · **Spec**: [spec.md](spec.md)

## Summary
Store the reviewed knowledge seeds and the guideline corpus where the meal check can use them: Neo4j for the food graph (dish → ingredient → component → Rule Card → paper) and Supabase Postgres for name search, Rule Cards and contextual hybrid RAG over guideline chunks. Expose the graph through the read-only `happygut-foodgraph` MCP server.

## Technical Context
- **Language**: Python 3.11 (pipelines, MCP server), SQL (Supabase migrations), Node 22 (migration tests with PGlite)
- **Dependencies**: PyYAML, neo4j driver, MCP Python SDK (FastMCP), sentence-transformers (G3 job), pgvector, pg_trgm
- **Storage**: Supabase Postgres (`knowledge`, `core`, `events`, `audit`, `cache` schemas), Neo4j AuraDB Free
- **Testing**: pytest (pipelines, MCP server on an in-memory graph), node:test + PGlite (migrations, RLS, hybrid search)
- **Constraints**: free tiers only; no network to Supabase/Neo4j from the build sandbox, so everything is tested locally and applied from Windows; GPU work runs as finite Ubuntu jobs (G1 headers, G2 aliases, G3 embeddings) that exchange files via git

## Constitution Check
| Principle | How this plan complies |
|---|---|
| II Safety | Rule Card `hard` flag and stricture rules carried into Neo4j and Postgres unchanged; only `approved` items load |
| III LLM never decides | Knowledge layer only retrieves; the engine decides |
| IV Evidence or Not sure | Every chunk and Rule Card keeps source, licence and quote; weak retrieval is flagged |
| V Privacy | RLS on every table; knowledge tables hold no patient data; app tables are not exposed through the Data API |
| VII Measured | Retrieval ablation (naive vs contextual vs hybrid vs rerank) recorded |
| VIII Free and simple | One Supabase project, one Neo4j instance; GPU jobs are finite |

## Project Structure
```
supabase/migrations/        SQL migrations (schema, RLS, search functions); supabase-only extras separate
supabase/tests/             PGlite tests for migrations, RLS isolation and search functions
pipelines/src/happygut_pipelines/
  seeds.py                  (done) load + validate seeds
  graph.py                  seeds → graph model, Cypher statements, in-memory graph for tests
  corpus.py                 source registry (licence gate), structure-aware chunking
  gpu_jobs.py               G1 headers, G2 aliases, G3 embeddings (run on Ubuntu, outputs to data/gpu_jobs/)
  load.py                   load seeds + GPU-job outputs into Neo4j and Supabase (run on Windows)
services/mcp/foodgraph/     FastMCP server: search_dish, get_components, explain_verdict_path
```
