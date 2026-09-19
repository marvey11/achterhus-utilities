#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
SYSTEMD_DIR=$(realpath "${SCRIPT_DIR}/../systemd")
CONFIG_DIR="${HOME}/.config/achterhus/photo-router"
USER_SYSTEMD_DIR="${HOME}/.config/systemd/user"

mkdir -p "${USER_SYSTEMD_DIR}" "${CONFIG_DIR}"

if [[ ! -f "${CONFIG_DIR}/env" ]]; then
    cp "${SYSTEMD_DIR}/env.example" "${CONFIG_DIR}/env"
    echo "Created ${CONFIG_DIR}/env from the example template. Update it before enabling the timer."
fi

# Symlink unit files so updates in the repository are reflected automatically.
ln -sfn "${SYSTEMD_DIR}/photo-router.service" "${USER_SYSTEMD_DIR}/photo-router.service"
ln -sfn "${SYSTEMD_DIR}/photo-router.timer" "${USER_SYSTEMD_DIR}/photo-router.timer"

systemctl --user daemon-reload
systemctl --user enable --now photo-router.timer
