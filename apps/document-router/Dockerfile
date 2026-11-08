# ==========================================
# Stage 1: Build & Dependency Resolution
# ==========================================
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

COPY apps/document-router/pyproject.toml apps/document-router/uv.lock \
    apps/document-router/README.md ./apps/document-router/
COPY libs/core/pyproject.toml libs/core/README.md ./libs/core/
COPY libs/core/src ./libs/core/src

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --project apps/document-router --locked --no-dev --no-editable \
    --no-install-project

COPY apps/document-router/src ./apps/document-router/src

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --project apps/document-router --locked --no-dev --no-editable

FROM python:3.14-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN groupadd -g 1000 appuser && useradd -r -u 1000 -g appuser appuser

COPY --from=builder /app/.venv /app/.venv

USER appuser

ENTRYPOINT ["document-router"]
CMD ["/source", "/target"]
