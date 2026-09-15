#!/usr/bin/env bash
# Build and run on a machine that already has ROS 2.
#   bash setup.sh video10.mp4
set -e
VIDEO=""
[ -n "${1:-}" ] && VIDEO="$(realpath "$1")"
HERE="$(cd "$(dirname "$0")" && pwd)"

source /opt/ros/*/setup.bash
sudo apt-get install -y "ros-$ROS_DISTRO-cv-bridge" python3-opencv python3-colcon-common-extensions
mkdir -p ~/ros2_ws/src
rm -rf ~/ros2_ws/src/pennair_ros2 ~/ros2_ws/build ~/ros2_ws/install ~/ros2_ws/log
cp -r "$HERE/pennair_ros2" ~/ros2_ws/src/
cp "$HERE/algorithm.py" ~/ros2_ws/src/pennair_ros2/pennair_ros2/   # single source of truth
cd ~/ros2_ws
colcon build --packages-select pennair_ros2
source install/setup.bash
[ -n "$VIDEO" ] && exec ros2 launch pennair_ros2 pennair.launch.py video:="$VIDEO"
