# Tasks: Knowledge layer

**Spec**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

## Phase 1: Storage
- [x] T001 Supabase migration: schemas, tables, indexes, partitions, RLS, grants (`supabase/migrations/`)
- [x] T002 Search functions: `knowledge.resolve_dish` (trigram over names/aliases) and `knowledge.hybrid_search` (vector + full text, Reciprocal Rank Fusion)
- [x] T003 PGlite test suite: migration applies cleanly, RLS isolates patients, search functions rank correctly
- [x] T004 Supabase-only migration: `pg_cron` jobs for cache expiry and photo retention

## Phase 2: Graph [US1, US2, US4]
- [x] T005 Graph model from seeds: nodes, relationships, Cypher statements with constraints and full-text index
- [x] T006 In-memory graph with the same queries, for tests and the MCP server's offline mode
- [x] T007 `happygut-foodgraph` MCP server (FastMCP): `search_dish`, `get_components`, `explain_verdict_path`; read-only; stdio + Streamable HTTP

## Phase 3: Guideline corpus [US3]
- [ ] T008 Source registry with licence gate (full text only for open licences; otherwise Rule Cards only)
- [ ] T009 Structure-aware chunker (section → paragraph, tables kept whole, 200–500 tokens)
- [~] T010 GPU job framework (framework done; G1 waits for the corpus) (`data/gpu_jobs/<job>/input|output`, provenance metadata) + G1 contextual headers (Qwen3 14B via Ollama)
- [x] T011 G2 Bangla/Banglish alias candidates (Gemma 3 12B, 3 seeded samples, keep ≥ 2 votes) → review file
- [x] T012 G3 corpus embeddings (BGE-M3 on ROCm PyTorch) → JSONL with float16 base64 vectors; reuses vectors for unchanged texts

## Phase 4: Load and verify
- [ ] T013 Loader (Windows): approved seeds + GPU-job outputs → Neo4j and Supabase
- [ ] T014 Retrieval evaluation: 30-question set, Recall@5, ablation table
  - Baseline (2026-10-22, G3 run on seeds before alias review): each dish's Bangla name → nearest English/Banglish name with plain BGE-M3 is the same dish for 55/61 (90%). Misses are sound-alikes (মুড়ি → murgi) and shared words (বেগুন ভাজা → beef bhuna). Target: hybrid trigram + vector beats this; G6 fine-tune beats both.
