from __future__ import annotations

from pathlib import Path  # noqa: TC003

from PIL import Image
from pytest import MonkeyPatch  # noqa: TC002
from typer.testing import CliRunner

from photo_router.main import app, organize_photos_secure


def test_organize_photos_secure_moves_jpegs_into_year_directories(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    destination_dir = tmp_path / "destination"

    jpg_path = source_dir / "vacation.jpg"
    exif = Image.Exif()
    exif[36867] = "2024:06:15 12:34:56"
    image = Image.new("RGB", (10, 10), color="blue")
    image.save(jpg_path, exif=exif)

    png_path = source_dir / "not-a-photo.png"
    Image.new("RGB", (10, 10), color="red").save(png_path)

    organize_photos_secure(source_dir, destination_dir)

    assert not jpg_path.exists()
    assert (destination_dir / "2024" / "vacation.jpg").exists()
    assert png_path.exists()


def test_cli_accepts_source_and_destination_arguments(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    source_dir = tmp_path / "source"
    destination_dir = tmp_path / "destination"
    source_dir.mkdir()
    destination_dir.mkdir()

    captured: dict[str, Path] = {}

    def fake_organize(source: Path, target: Path) -> None:
        captured["source"] = source
        captured["target"] = target

    monkeypatch.setattr("photo_router.main.organize_photos_secure", fake_organize)

    result = CliRunner().invoke(
        app,
        ["--source-dir", str(source_dir), "--destination-dir", str(destination_dir)],
    )

    assert result.exit_code == 0
    assert captured == {"source": source_dir, "target": destination_dir}
