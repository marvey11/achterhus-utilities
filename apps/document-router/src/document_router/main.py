"""Typer CLI interface for Achterhus Document Router."""

from pathlib import Path
from typing import Annotated

import typer
from core.telemetry import telemetry_context
from rich.console import Console
from rich.table import Table

from document_router.core.engine import DocumentRouterEngine

app = typer.Typer(
    name="document-router",
    help="Route and organize drop-zone documents for Achterhus home server.",
    add_completion=False,
)

SERVICE_NAME = "document-router"

stdout_console = Console()
stderr_console = Console(stderr=True)


@app.command()
def main(
    source_dir: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Source drop-zone directory containing provider subfolders.",
        ),
    ],
    target_dir: Annotated[
        Path,
        typer.Argument(
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Base target directory for permanent storage.",
        ),
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Simulate operations without altering files on disk.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable detailed logging output.",
        ),
    ] = False,
) -> None:
    """Parse drop-zone documents and execute routing jobs."""
    try:
        engine = DocumentRouterEngine(source_dir, target_dir, dry_run=dry_run)
        with telemetry_context(SERVICE_NAME) as telemetry:
            jobs = engine.discover_and_plan()
            action_counts = {
                "moved_count": 0,
                "copied_count": 0,
                "ignored_count": 0,
                "quarantined_count": 0,
            }

            if not jobs:
                stdout_console.print("No matchable documents found to route.")
            else:
                table = Table(
                    title="Document Routing Execution Plan"
                    if dry_run
                    else "Routing Execution Summary"
                )
                table.add_column("Source File", style="cyan")
                table.add_column("Provider", style="magenta")
                table.add_column("Action Result", style="green")

                for job in jobs:
                    result_summary = engine.processor.execute_job(job)
                    table.add_row(
                        job.source_file_path.name,
                        job.metadata.provider,
                        result_summary,
                    )
                    if result_summary.startswith("MOVE ->"):
                        action_counts["moved_count"] += 1
                    elif result_summary.startswith("COPY ->"):
                        action_counts["copied_count"] += 1
                    elif result_summary.startswith("IGNORE"):
                        action_counts["ignored_count"] += 1
                    else:
                        action_counts["quarantined_count"] += 1

                stdout_console.print(table)

            if telemetry is not None:
                telemetry.set_metrics(
                    {"job_count": len(jobs), **action_counts, "dry_run": dry_run}
                )

    except Exception as err:
        stderr_console.print(f"[bold red]Error:[/bold red] {err}")
        if verbose:
            stderr_console.print_exception()
        raise typer.Exit(code=1) from err


if __name__ == "__main__":
    app()
