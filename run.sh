#!/usr/bin/env bash
# Play the detector locally, no ROS. Creates the venv on first run.
#   bash run.sh video10.mp4
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
if [ ! -d "$HERE/.venv" ]; then
    python3 -m venv "$HERE/.venv"
    "$HERE/.venv/bin/pip" install --quiet --upgrade pip
    "$HERE/.venv/bin/pip" install --quiet opencv-python numpy
fi
exec "$HERE/.venv/bin/python" "$HERE/demo.py" "$@"
