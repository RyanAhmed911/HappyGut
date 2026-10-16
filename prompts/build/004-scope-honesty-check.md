# P-004: Scope and honesty check
- **Category:** Planning / Review
- **Tool:** Claude Code
- **Date:** 2026-09-24

## Prompt
> By the way, the requirements mostly say only 1 or 2 needed, why are we selecting almost all of them?

## Output
A team rule: tick an item only if it earns points **and** will really exist by Oct 31. The data stack was cut from 8 services to 3 (Supabase, Neo4j, local Python), with an authoritative prototype list (`docs/03-data.md` §0) and a separate Finals list. Human review caught AI over-scoping before any code was written.
