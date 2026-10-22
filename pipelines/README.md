# pipelines: knowledge build

crawl → parse → resolve → enrich → load (bronze → silver → gold → Neo4j / pgvector). Idempotent steps, run with `make knowledge`. Sources and licences: `docs/03-data.md`.
