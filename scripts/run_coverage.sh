#!/usr/bin/env bash
set -euo pipefail

echo "Running full test suite with coverage..."

# Run pytest with explicit coverage flags and coverage threshold check
uv run pytest \
  --cov=apps \
  --cov=libs \
  --cov-report=term-missing \
  --cov-fail-under=80

echo "✅ All tests passed with sufficient coverage."
