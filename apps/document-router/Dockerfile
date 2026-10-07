# ==========================================
# Stage 1: Build & Dependency Resolution
# ==========================================
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY apps/document-router/pyproject.toml apps/document-router/README.md \
    ./apps/document-router/
COPY libs/core/pyproject.toml libs/core/README.md ./libs/core/
COPY libs/core/src ./libs/core/src

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --no-install-workspace \
    --package document-router

COPY apps/document-router/src ./apps/document-router/src

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --package document-router

FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN groupadd -g 1000 appuser && useradd -r -u 1000 -g appuser appuser

COPY --from=builder /app/.venv /app/.venv

USER appuser

ENTRYPOINT ["document-router"]
CMD ["/source", "/target"]
