# Photo Router

Photo Router is a small CLI utility for moving JPEG photos from a source directory to a long-term archive structure. It reads the EXIF `DateTimeOriginal` metadata, groups files by year, and moves each file into a destination directory such as `2024/`.

## What it does

- Scans a source directory recursively for `.jpg` and `.jpeg` files.
- Reads the EXIF date from each image.
- Creates a year-based destination folder under the configured base archive path.
- Moves the file into place using an atomic move operation with integrity verification.
- Logs progress and warnings to stdout/stderr so it works well in a containerized `systemd` service environment.

## Usage

```bash
# photo-router <source_dir> <target_dir>
photo-router /mnt/card /srv/photos
```

This will scan the source directory, move each photo into a matching year folder under the target, and keep the original file name unless a collision occurs.

## Example output

```text
Routed DSC_0001.jpg to 2024/DSC_0001.jpg (integrity verified)
Pipeline finished! Moved 27 files. Skipped/failed: 2.
```

## Requirements

- Python 3.12+
- The project dependencies are managed by `uv`.
- The app expects a real photo source directory containing JPEG files with EXIF metadata.

## Docker image

The application is available as a Docker image. The GitHub Actions workflow builds and publishes it to GitHub Container Registry.

```bash
docker pull ghcr.io/marvey11/achterhus-utilities/photo-router:latest
```
