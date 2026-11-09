# Utility Scripts

Run scripts from the repository root.

* `bootstrap.sh` -- locks and syncs every app environment, then installs the pre-commit and pre-push Git hooks. Install `uv` first, then run `./scripts/bootstrap.sh` after cloning.
* `check-locks.sh` -- verifies that every app lockfile matches its project manifest.
* `run-coverage.sh` -- runs each application's test suite with shared-library coverage, combines the coverage data, and enforces a repo-wide threshold. Pass `--html`, `--xml`, or `--all` to generate reports.
* `run-mypy.sh` -- runs mypy against each application and the shared library.
* `run-pyright.sh` -- runs Pyright against each application and the shared library.
