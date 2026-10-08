from __future__ import annotations

from pathlib import Path  # noqa: TC003
from typing import TYPE_CHECKING

import pytest
from PIL import Image
from typer.testing import CliRunner

from photo_router.main import app, organize_photos_secure

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_organize_photos_secure_moves_jpegs_into_year_directories(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    target_dir = tmp_path / "target"

    jpg_path = source_dir / "vacation.jpg"
    exif = Image.Exif()
    exif[36867] = "2024:06:15 12:34:56"
    image = Image.new("RGB", (10, 10), color="blue")
    image.save(jpg_path, exif=exif)

    png_path = source_dir / "not-a-photo.png"
    Image.new("RGB", (10, 10), color="red").save(png_path)

    organize_photos_secure(source_dir, target_dir)

    assert not jpg_path.exists()
    assert (target_dir / "2024" / "vacation.jpg").exists()
    assert png_path.exists()


def test_organize_photos_secure_skips_jpegs_missing_exif(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    target_dir = tmp_path / "target"

    jpg_path = source_dir / "vacation.jpg"
    Image.new("RGB", (10, 10), color="blue").save(jpg_path)

    organize_photos_secure(source_dir, target_dir)

    assert jpg_path.exists()
    assert not (target_dir / "2024").exists()


def test_organize_photos_secure_raises_for_missing_source_dir(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "missing"
    target_dir = tmp_path / "target"

    with pytest.raises(FileNotFoundError, match="Source directory does not exist"):
        organize_photos_secure(source_dir, target_dir)


def test_organize_photos_secure_raises_for_file_source_path(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source.txt"
    source_dir.write_text("not a directory")
    target_dir = tmp_path / "target"

    with pytest.raises(NotADirectoryError, match="Source path is not a directory"):
        organize_photos_secure(source_dir, target_dir)


def test_cli_accepts_source_and_target_arguments(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    source_dir = tmp_path / "source"
    target_dir = tmp_path / "target"
    source_dir.mkdir()
    target_dir.mkdir()

    captured: dict[str, Path] = {"source": source_dir, "target": target_dir}

    mocker.patch("photo_router.main.organize_photos_secure", return_value=captured)

    result = CliRunner().invoke(
        app,
        [str(source_dir), str(target_dir)],
    )

    assert result.exit_code == 0
    assert captured == {"source": source_dir, "target": target_dir}
