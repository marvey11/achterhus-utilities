#!/usr/bin/env bash
set -euo pipefail

# Determine which apps to run on
if [ $# -gt 0 ]; then
    APPS=("$1")
    # Validate that the requested app directory exists
    if [ ! -d "apps/${APPS[0]}" ]; then
        echo "Error: App directory 'apps/${APPS[0]}' does not exist." >&2
        exit 1
    fi
else
    # Dynamically discover all apps for future-proofing if no argument is passed
    APPS=()
    for dir in apps/*/; do
        if [ -d "$dir" ]; then
            APPS+=("$(basename "$dir")")
        fi
    done
fi

for app in "${APPS[@]}"; do
    echo "==> Running mypy for $app..."
    uv run --project "apps/$app" mypy \
      "apps/$app/src" "apps/$app/tests" \
      libs/core/src libs/core/tests
done
