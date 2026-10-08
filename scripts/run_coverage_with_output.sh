#!/usr/bin/env bash
set -euo pipefail

echo "Running full test suite with coverage..."

# Run pytest with explicit coverage flags
uv run pytest \
  --cov=apps \
  --cov=libs \
  --cov-report=term-missing \
  --cov-report=html \
  --cov-report=xml

echo "✅ All tests passed with sufficient coverage."
