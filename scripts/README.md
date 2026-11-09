# Utility Scripts

This folder contains the following scripts:

* `bootstrap.sh` -- locks and syncs every app's uv environment, then installs the pre-commit and pre-push Git hooks. Install `uv` first, then run `./scripts/bootstrap.sh` after cloning.
* `check-locks.sh` -- verifies that every app lockfile matches its project manifest.
* `run-coverage.sh` -- runs each app's tests and checks combined coverage; can optionally write XML and/or HTML output (off by default)
* `run-mypy.sh` -- runs mypy against each application and the shared library.
* `run-pyright.sh` -- runs Pyright against each application and the shared library.
