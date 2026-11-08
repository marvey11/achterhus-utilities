#!/usr/bin/env bash
set -euo pipefail

uv run --project apps/document-router pyright \
  apps/document-router libs/core
uv run --project apps/photo-router pyright \
  apps/photo-router libs/core
