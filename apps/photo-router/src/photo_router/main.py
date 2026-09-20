from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path  # noqa: TC003
from typing import Annotated, Final

import typer
from codescape.util.fileutils import atomic_move
from PIL import Image
from rich.console import Console
from rich.logging import RichHandler
from telemetry.client import TelemetryClient

app = typer.Typer(
    add_completion=False,
    help="Safely route JPEG photos into year-based folders.",
)


TELEMETRY_API = os.getenv("TELEMETRY_API_URL", "http://localhost:8000")

SERVICE_NAME = "photo-router"

DATE_TAG_ID: Final[int] = 36867  # DateTimeOriginal
LOGGER = logging.getLogger("photo_router")


def configure_logging() -> None:
    """Configure structured, stream-only logging for containerized execution."""
    if LOGGER.handlers:
        return

    console = Console(stderr=True)
    handler = RichHandler(
        console=console,
        markup=False,
        rich_tracebacks=True,
        show_path=False,
    )
    handler.setFormatter(logging.Formatter("%(message)s"))

    LOGGER.setLevel(logging.INFO)
    LOGGER.addHandler(handler)
    LOGGER.propagate = False


def _resolve_photo_year(date_value: object) -> str:
    """Convert EXIF DateTimeOriginal values into the target year folder name."""
    if isinstance(date_value, datetime):
        return date_value.strftime("%Y")

    if not isinstance(date_value, str):
        date_value = str(date_value)

    try:
        parsed_date = datetime.strptime(date_value, "%Y:%m:%d %H:%M:%S")
    except ValueError as exc:
        msg = f"Invalid EXIF timestamp: {date_value!r}"
        raise ValueError(msg) from exc

    return parsed_date.strftime("%Y")


def _new_target_path(target_dir: Path, source_file: Path) -> Path:
    """Return a unique target path, preserving the original filename when possible."""
    candidate = target_dir / source_file.name
    if not candidate.exists():
        return candidate

    file_id = source_file.stat().st_mtime_ns
    return target_dir / f"{source_file.stem}_{file_id}{source_file.suffix}"


def organize_photos_secure(source_dir: Path, destination_dir: Path) -> None:
    """Move JPEG photos into year-based directories while validating EXIF metadata."""
    configure_logging()

    if not source_dir.exists():
        msg = f"Source directory does not exist: {source_dir}"
        raise FileNotFoundError(msg)
    if not source_dir.is_dir():
        msg = f"Source path is not a directory: {source_dir}"
        raise NotADirectoryError(msg)

    destination_dir.mkdir(parents=True, exist_ok=True)

    with TelemetryClient(TELEMETRY_API, service_name=SERVICE_NAME) as telemetry:
        success_count = 0
        skipped_count = 0

        for file_path in sorted(source_dir.rglob("*")):
            if not file_path.is_file() or file_path.suffix.lower() not in {
                ".jpg",
                ".jpeg",
            }:
                continue

            try:
                with Image.open(file_path) as image:
                    exif_data = image.getexif()
                    date_value = exif_data.get(DATE_TAG_ID) if exif_data else None

                if date_value is None:
                    LOGGER.warning(
                        "Skipped %s: missing EXIF DateTimeOriginal metadata.",
                        file_path.name,
                    )
                    skipped_count += 1
                    continue

                year = _resolve_photo_year(date_value)
                target_dir = destination_dir / year
                target_dir.mkdir(parents=True, exist_ok=True)
                target_file_path = _new_target_path(target_dir, file_path)

                atomic_move(file_path, target_file_path, verify_hash=True)
                success_count += 1
                LOGGER.info(
                    "Routed %s to %s (integrity verified)",
                    file_path.name,
                    target_file_path.relative_to(destination_dir),
                )
            except (FileNotFoundError, OSError, ValueError, TypeError) as exc:
                LOGGER.exception("Failed to process %s: %s", file_path.name, exc)
                skipped_count += 1

        telemetry.set_metrics(
            {"success_count": success_count, "skipped_count": skipped_count}
        )

        LOGGER.info(
            "Pipeline finished! Moved %s files. Skipped/failed: %s.",
            success_count,
            skipped_count,
        )


@app.command()
def main(
    source_dir: Annotated[
        Path,
        typer.Option(
            ...,
            "--source-dir",
            help="Directory containing the photo files to route.",
        ),
    ],
    destination_dir: Annotated[
        Path,
        typer.Option(
            ...,
            "--destination-dir",
            help="Base destination directory for the organized photos.",
        ),
    ],
) -> None:
    """Safely move JPEG photos from a source card to a structured archive."""
    organize_photos_secure(source_dir, destination_dir)


if __name__ == "__main__":
    app()
