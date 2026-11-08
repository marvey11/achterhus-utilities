#!/usr/bin/env bash
set -euo pipefail

uv run --project apps/document-router mypy \
  apps/document-router/src apps/document-router/tests \
  libs/core/src libs/core/tests
uv run --project apps/photo-router mypy \
  apps/photo-router/src apps/photo-router/tests \
  libs/core/src libs/core/tests
