# ==========================================
# Stage 1: Build & Dependency Resolution
# ==========================================
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy workspace metadata files to cache dependency installation
COPY pyproject.toml uv.lock ./
COPY apps/photo-router/pyproject.toml apps/photo-router/README.md ./apps/photo-router/
# Copy full source code for workspace packages
COPY apps/photo-router/src ./apps/photo-router/src

# Perform final sync to install workspace packages into environment
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync \
    --frozen \
    --no-dev \
    --no-editable \
    --package photo-router

# ==========================================
# Stage 2: Production Runtime
# ==========================================
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Create a non-root user for runtime security
RUN groupadd -g 1000 appuser && \
    useradd -r -u 1000 -g appuser appuser

# Copy installed virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Define volume mount points
VOLUME ["/source", "/target"]

USER appuser

ENTRYPOINT ["photo-router"]
CMD ["--source-dir", "/source", "--destination-dir", "/target"]
