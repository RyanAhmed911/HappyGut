# HappyGut: Claude Code context

@AGENTS.md

## Claude Code specifics
- Project skills live in `.claude/skills/`: Spec-Kit (`speckit-*`) plus HappyGut procedures (`add-dish`, `add-rule-card`, `new-prompt-version`, `run-evals`).
- Ask before any write or execute call through MCP servers (Supabase, Neo4j); use the dev projects only.
- Stay on the session's assigned git branch; Spec-Kit tracks the active feature in `.specify/feature.json`, not by branch.
