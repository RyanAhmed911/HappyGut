# P-003: Data lifecycle design
- **Category:** Data architecture
- **Tool:** Claude Code
- **Date:** 2026-09-24

## Prompt
> Let's start with Data Lifecycle and engineering, where we show your full AI-native data stack — acquisition, parsing, storage, visualization, ML/insights, outbound APIs, and governance. 1. Data Sources: Where does your data come from? Select all that apply. *[portal options]* And then, list the specific sources.

Follow-up prompts in the same session covered acquisition, parsing, storage, visualization, insights, orchestration, outbound APIs, governance and tunnelling.

## Output
A full data lifecycle design (`docs/03-data.md`):
- source catalogue with licences and tiers
- explicit exclusions (proprietary FODMAP database, social media, real patient records)
- scrapers and parsers
- Postgres / pgvector / Neo4j / Delta schemas, partitioning, indexes and retention
- ML and statistical methods
- privacy, quality and lineage controls
