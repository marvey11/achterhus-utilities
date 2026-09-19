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
photo-router --source-dir /mnt/card --destination-dir /srv/photos
```

This will scan the source directory, move each photo into a matching year folder under the destination, and keep the original file name unless a collision occurs.

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

## Running as a `systemd` service

The `*.service` and `*.timer` units are stored in the `systemd` folder. Both the photo source directory, the archive target directory, and the Docker image can be configured via `~/.config/achterhus/photo-router/env`. An example configuration is available in `systemd/env.example`.

The install helper script is `scripts/install_systemd.sh`. Run it from the repository root:

```bash
bash apps/photo-router/scripts/install_systemd.sh
```

The script creates the required configuration directory, copies the example environment file when needed, and installs the timer units into the user systemd directory.

Useful `systemctl` commands:

```bash
# Reload systemd to discover the new unit files
systemctl --user daemon-reload

# Test the service execution manually once
systemctl --user start photo-router.service

# Check execution logs to verify success
journalctl --user -u photo-router.service

# Enable and start the timer
systemctl --user enable --now photo-router.timer

# Check upcoming timer runs
systemctl --user list-timers

# Verify timer status
systemctl --user status photo-router.timer

# Enable lingering so the user-level service runs while you are logged out
loginctl enable-linger "$USER"
```
