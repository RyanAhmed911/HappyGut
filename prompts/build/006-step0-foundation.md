# P-006: Step 0 foundation
- **Category:** Architecture / Project setup
- **Tool:** Claude Code + GitHub Spec-Kit (`specify init --integration claude`)
- **Date:** 2026-10-21

## Prompt
> Now, we have to start actually building the project step by step. What is the first step?
>
> *(follow-ups)* Yes, but before doing that, keep in mind that we won't use anything that is paid and requires card information, like google cloud.

## Output
- Free-only service audit: Cloudflare Tunnel/R2 replaced by Tailscale Funnel + Supabase Storage; backend pinned to Hugging Face Spaces
- `docs/portal/submission-scope.md`: A/B/C tiers and reconciliation checklist
- `docs/02-architecture.md`: system, hero-flow sequence, verdict engine algorithm, decision log
- Spec-Kit constitution (8 principles) and specs 001 (knowledge layer), 002 (meal check)
- `AGENTS.md`, project skills (add-dish, add-rule-card, new-prompt-version, run-evals)
- Repo skeleton, `docker-compose.yml`, Caddy API-key gateway (validated: health 200, missing/wrong key 401), `docs/setup.md`
