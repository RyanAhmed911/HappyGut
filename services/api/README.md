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

## Check the AI models
```bash
uv run python -m happygut_api.diagnose
```
Models are picked automatically: at start-up the backend lists the models each key can use (Gemini on the `v1beta` API) and replaces any configured name that isn't available, logging what it chose; `/v1/health` shows the chosen names. `--list` prints what each key can use.

It shows whether each key is read and which models will be used, then calls each of them on its own (text, photo, explanation) and prints the provider's exact error with a hint when one fails. Pass a photo path to test with your own picture, or `--model <name>` to try another model. Key values are never printed. When a model fails during normal use, the backend window logs the same one-line reason (`perception failed: …`).

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
