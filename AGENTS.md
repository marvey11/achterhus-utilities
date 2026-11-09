# AGENTS.md

## Repository Overview

`achterhus-utilities` is a Python 3.14+ monorepo managed by `uv`. The independent
worker applications live under `apps/`; shared code lives under `libs/`.

- `apps/document-router`: routes supported documents to permanent storage.
- `apps/photo-router`: routes digital JPEG photos into year-based archive folders.
- `libs/core`: local library providing the shared telemetry context manager.

Each application is an independent uv project with its own `pyproject.toml`,
`uv.lock`, and virtual environment. Both apps consume `libs/core` as a local path
dependency. The root `pyproject.toml` contains shared tool configuration only; it
is not a uv project or workspace.

The repository uses a `src` layout. Import packages through their installed package
names, not by reaching into source directories with relative filesystem assumptions.

## Source Boundaries

- Put reusable functionality shared by multiple applications in `libs/core/src/core`.
- Keep application-specific behavior in that application's `src/` package.
- Keep tests next to the package they validate, under its `tests/` directory.
- Preserve public service and repository APIs unless the task explicitly requires a
  contract change.

## Development Conventions

- Target Python 3.14 or newer.
- Use 4 spaces and a maximum line length of 88 characters.
- Use double-quoted strings, consistent with Ruff format configuration.
- Add explicit annotations for functions, parameters, and return values.
- Prefer `typing.Annotated` for Typer command arguments and options when defining
  CLI metadata.
- Use Rich `Console` instances for CLI output. Use a stderr console for warnings
  and errors and a stdout console for normal output.
- Preserve command exit codes and user-visible output unless changing the CLI
  contract is part of the task.
- Raise exceptions with `from err` when converting an underlying error at a
  boundary, such as a CLI handler.
- Avoid broad refactors and unrelated formatting changes.
- Add comments only when they explain a non-obvious decision.

## Install and Run

Install each application's dependencies independently:

```sh
uv sync --project apps/document-router --locked --group dev
uv sync --project apps/photo-router --locked --group dev
```

Run a CLI through its own environment:

```sh
uv run --project apps/document-router document-router /source /target
uv run --project apps/photo-router photo-router /source /target
```

When changing an app's dependencies, regenerate its lockfile with
`uv lock --project apps/<application>` and commit the corresponding
`apps/<application>/uv.lock`. Do not add a root lockfile or merge the app
dependency graphs.

## Tests and Quality Checks

The authoritative CI workflow is [.github/workflows/ci.yml](.github/workflows/ci.yml).
It syncs both app environments and runs the same pre-commit hooks used locally:

```sh
uv run --project apps/document-router pre-commit run --all-files
```

The hooks cover generic file checks, Bash, Markdown, Ruff lint/format, and Python
type checks. Run the full test suite with its repository-wide coverage threshold:

```sh
./scripts/run-coverage.sh
uv run --project apps/document-router pytest -o addopts='' \
  apps/document-router/tests libs/core/tests
uv run --project apps/photo-router pytest -o addopts='' \
  apps/photo-router/tests
```

`scripts/run-mypy.sh` and `scripts/run-pyright.sh` run each app's type checker in
both relevant project environments. Their pre-commit hooks run both scripts.

For a focused test, use the relevant app environment and test path, for example:

```sh
uv run --project apps/photo-router pytest -o addopts='' \
  apps/photo-router/tests/test_main.py
```

Do not weaken lint, type, test, or coverage checks to make a change pass. Keep the
pre-commit and CI check paths aligned.

## Docker and Releases

Build an application image from the repository root:

```sh
docker build -f apps/document-router/Dockerfile -t document-router .
docker build -f apps/photo-router/Dockerfile -t photo-router .
```

The images use Python 3.14 and install only the selected app's locked dependencies.
Pushing a tag named `<application-name>-v<major>.<minor>.<patch>`, such as
`photo-router-v1.2.3`, automatically creates a GitHub Release with generated
notes and publishes an image with full, `major.minor`, and `major`
semantic-version tags. Existing full-version images are immutable and skipped;
the floating aliases can advance. `latest` is reserved for pushes to `main`.

## Change Workflow

1. Inspect repository status and applicable instructions before editing.
2. Read the owning implementation and neighboring tests.
3. Make the smallest change that addresses the requested behavior.
4. Run focused checks after the first edit.
5. Run the relevant app checks and repository-wide coverage for shared changes.
6. Review `git diff` and ensure generated artifacts or unrelated files are not
   included.
