# services/api: FastAPI backend

`/v1` REST API with a streamed meal check. A LangGraph graph runs the hero flow (red-flag sentinel → PII scrub → perception → dish resolution → **verdict engine** → cited explanation → output guard → store). Pydantic-AI agents do perception and explanation on Gemini (Google AI Studio) with a fallback model; the verdict always comes from `engine/`. Design: [`specs/002-meal-check/plan.md`](../../specs/002-meal-check/plan.md).

## Run on Windows (development)
```bash
cd services/api
uv sync --group dev --extra pii
uv run --group dev pytest -q
uv run uvicorn --factory happygut_api.main:app --reload --port 8000
```
Settings come from the repo-root `.env` (see `.env.example`). Without `SUPABASE_DB_URL` the API keeps data in memory. Until seeds are approved, set `INCLUDE_DRAFT_SEEDS=true` to try it; every verdict then carries an "unreviewed knowledge" note.

## Endpoints
| Method | Path | What it does |
|---|---|---|
| GET | `/v1/health` | Status, engine version, how much knowledge is loaded |
| POST | `/v1/meal-checks` | Multipart: `text` and/or `image`, optional `lang` (`bn`/`en`). Streams Server-Sent Events: `dishes` → `verdict` → `explanation` → `done`, or a single `red_flag`, `not_food` or `error` event |
| GET | `/v1/meal-checks/{id}` | A stored meal check (own only) |
| POST | `/v1/meal-checks/{id}/feedback` | `{"answer": "right" \| "wrong" \| "not_sure"}` |

All `/v1` calls except health need `Authorization: Bearer <Supabase access token>` and a row in `core.patients`.

The browser calls `POST /v1/meal-checks` with `fetch` and reads the body as a stream (EventSource can't send a photo).

## Deploy (Hugging Face Spaces, Docker, free CPU)
Build context is the repo root: `docker build -f services/api/Dockerfile -t happygut-api .`. Put the `.env` values in the Space's **Secrets**, never in the image.

## Safety and privacy notes
- The red-flag sentinel runs on the raw text before any model sees it; a hit stops the flow and is stored in `events.red_flag_events`.
- Text is scrubbed before any cloud call: Bangladesh rules always, Presidio (English names and places) in the Docker image, and a Bengali NER model once one is chosen and its licence recorded. Dish names and aliases are protected from the model-based layers.
- Photos are re-encoded without EXIF/GPS before they're sent anywhere. They aren't stored yet.
- Explanations must cite IDs from the evidence packet, may not state a verdict label, and may not use "safe" or medication words. After two failures the deterministic template is used.
