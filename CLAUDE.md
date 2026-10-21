# HappyGut: Claude Code context

@AGENTS.md

## Claude Code specifics
- Project skills live in `.claude/skills/`: Spec-Kit (`speckit-*`) plus HappyGut procedures (`add-dish`, `add-rule-card`, `new-prompt-version`, `run-evals`).
- Supabase and Neo4j MCP servers run read-only. Schema changes go through migration files (Supabase CLI) and graph changes through the seed files, both reviewed in PRs. The single Supabase project and Neo4j instance hold simulated data only.
- Stay on the session's assigned git branch; Spec-Kit tracks the active feature in `.specify/feature.json`, not by branch.
