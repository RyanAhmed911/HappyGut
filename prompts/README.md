# Prompt library

Versioned prompts used to **design and build** HappyGut (build provenance), and prompts that **run inside** the product (runtime). Each file records its purpose, the tool, the date and what it produced.

| ID | File | Category | Purpose |
|---|---|---|---|
| P-001 | [`build/001-strategy-planning.md`](build/001-strategy-planning.md) | Planning | Step-by-step strategy from the participant guide + project context |
| P-002 | [`build/002-portal-narrative-rewrite.md`](build/002-portal-narrative-rewrite.md) | Documentation | Public summary, problem and solution rewrite |
| P-003 | [`build/003-data-lifecycle-design.md`](build/003-data-lifecycle-design.md) | Data architecture | Full data lifecycle design |
| P-004 | [`build/004-scope-honesty-check.md`](build/004-scope-honesty-check.md) | Review | Tick-only-if-real rule, lean prototype scope |
| P-005 | [`build/005-ai-architecture-design.md`](build/005-ai-architecture-design.md) | AI architecture | Prompts, models, RAG, MCP, agents, evaluation, guardrails |

Build-phase prompts (Spec-Kit specs, Lovable UI, /docs module, MCP servers) are added as they're used. Runtime prompts live in `runtime/`.
