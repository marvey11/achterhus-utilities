# Document Router

Safely organise documents into permanent storage. The router scans provider
subfolders under a source directory, parses supported documents, and then executes
the resulting routing jobs. Depending on the parser result, a document can be
moved, copied, ignored, or quarantined.

## Usage

```bash
document-router /path/to/source /path/to/target
```

Use `--dry-run` (or `-n`) to display the execution plan without changing files.
Use `--verbose` (or `-v`) to include a traceback when an error occurs.

The source directory should contain provider subfolders, such as `naturstrom/`,
`ryd/`, `scalable/`, or `vodafone/`. Files directly in the source root and files
inside unregistered provider folders are skipped.

## Docker

Build the image from the repository root:

```bash
docker build -f apps/document-router/Dockerfile -t document-router .
```

Mount the input and archive directories at `/source` and `/target`:

```bash
docker run --rm \
  -v /path/to/inbox:/source \
  -v /path/to/archive:/target \
  document-router
```

## Telemetry

When `SERVICE_RUN_ID` is set by the service orchestrator, the router reports `jobs`, `moved`, `copied`, `ignored`, `quarantined`, and `dry_run`. Set `TELEMETRY_API_URL` to select the telemetry service endpoint; it defaults to `http://localhost:8000`. Without a run ID, telemetry is disabled.
