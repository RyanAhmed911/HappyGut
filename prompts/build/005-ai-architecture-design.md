# P-005: AI architecture and usage design
- **Category:** AI architecture
- **Tool:** Claude Code
- **Date:** 2026-10-16

## Prompt
> Prompt Usage — How did you design prompts? Patterns used (few-shot, chain-of-thought, role prompting), iteration approach, prompt versioning. Token Optimization — Strategies to reduce cost & latency… LLMs / Models Used — Select all models used… How & why did you use these LLMs?

Follow-up prompts covered RAG, MCP servers, agent frameworks, fine-tuning, evaluation, guardrails, local LLMs, automation and AI-DLC.

## Output
The AI design (`docs/portal/ai-usage.md`):
- prompt design rules and versioning
- token-optimisation strategy for free-tier APIs
- model roles: Gemini, Llama, Gemma, Qwen, DeepSeek-R1-Distill, with a 12 GB VRAM loading plan
- hybrid contextual Graph RAG
- 5 MCP servers built + 5 used
- LangGraph + Pydantic-AI agent graph
- evaluation plan and guardrails
