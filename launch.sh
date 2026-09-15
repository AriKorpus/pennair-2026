#!/usr/bin/env bash
# Run the nodes after setup.sh has built them once.
#   bash launch.sh video10.mp4
set -e
VIDEO="$(realpath "${1:?usage: bash launch.sh <video>}")"
source ~/ros2_ws/install/setup.bash
ros2 launch pennair_ros2 pennair.launch.py video:="$VIDEO"
