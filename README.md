# Achterhus Utilities

A collection of utilities for the `achterhus` home server, packaged as
containerised worker services.

* [Document Router](apps/document-router/README.md) -- Safely organise documents into permanent storage.
* [Photo Router](apps/photo-router/README.md) -- Safely organise JPEG photos into year-based archive folders.

## Project structure

Each application under `apps/` is an independently managed `uv` project with its
own lockfile, development environment, and Docker image. The shared `core` package
under `libs/core/` is consumed as a local path dependency by each application; it
provides the shared telemetry context.

The root `pyproject.toml` contains repository-wide Ruff, mypy, Pyright, pytest, and
coverage configuration. It is not a uv workspace or a dependency project.

## Development

Use Python 3.14 or newer. Install and lock each app independently:

```bash
uv sync --project apps/document-router --locked --group dev
uv sync --project apps/photo-router --locked --group dev
```

Run an application from its environment:

```bash
uv run --project apps/document-router document-router /source /target
uv run --project apps/photo-router photo-router /source /target
```

Run the repository checks with:

```bash
uv run --project apps/document-router pre-commit run --all-files
./scripts/run-coverage.sh
```

Each application has its own usage instructions and Dockerfile. Images expect
input and destination directories to be mounted inside the container. Images are
published to `ghcr.io/marvey11/achterhus-utilities/<application>` when a
`<application>-vX.Y.Z` tag is pushed. The tag push automatically creates a
GitHub Release with generated notes. Release images receive `X.Y.Z`, `X.Y`, and
`X` tags. An existing `X.Y.Z` image is not rebuilt or overwritten; floating
`X.Y` and `X` tags can advance with later releases. `latest` is reserved for
builds from the `main` branch.
