# HappyGut API for Hugging Face Spaces (Docker SDK, free CPU). Build from the repo root:
#   docker build -f services/api/Dockerfile -t happygut-api .
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYDANTIC_AI_NO_BANNER=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PII_PRESIDIO=true

RUN pip install --no-cache-dir "uv==0.11.32" && useradd -m -u 1000 user
WORKDIR /app

# Only what the API needs: engine, pipelines (seed loader), the API, approved seeds, runtime prompts and the
# red-flag suite (for the weekly self-check job).
COPY engine/pyproject.toml engine/README.md engine/
COPY engine/src engine/src
COPY pipelines/pyproject.toml pipelines/
COPY pipelines/src pipelines/src
COPY services/api/pyproject.toml services/api/uv.lock services/api/README.md services/api/
COPY services/api/src services/api/src
COPY data/seeds data/seeds
COPY prompts/runtime prompts/runtime
COPY evals/sets evals/sets

RUN cd services/api && uv sync --frozen --no-dev --extra pii --extra tracing --python /usr/local/bin/python3.11 && chown -R user /app

USER user
EXPOSE 7860
HEALTHCHECK --interval=60s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/v1/health')"
CMD ["/app/services/api/.venv/bin/uvicorn", "--factory", "happygut_api.main:app", "--host", "0.0.0.0", "--port", "7860", "--proxy-headers"]
