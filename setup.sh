#!/usr/bin/env bash
# One-time: install ROS 2 and dependencies if missing, then build the package.
# Run once; use launch.sh after this to run the nodes.
#   bash setup.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"

# ROS 2 itself, if not already present
if [ -z "$(ls /opt/ros 2>/dev/null)" ]; then
    case "$(. /etc/os-release && echo "$VERSION_ID")" in
        22.04) ROS=humble ;;
        24.04) ROS=jazzy ;;
        26.04) ROS=lyrical ;;
        *) echo "No matching ROS 2 for this Ubuntu; install it manually, then re-run." >&2; exit 1 ;;
    esac
    sudo apt-get update
    sudo apt-get install -y locales curl software-properties-common
    sudo add-apt-repository -y universe
    V=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest \
        | grep -F '"tag_name"' | awk -F'"' '{print $4}')
    curl -L -o /tmp/ros2.deb \
        "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${V}/ros2-apt-source_${V}.$(. /etc/os-release && echo "$VERSION_CODENAME")_all.deb"
    sudo apt-get install -y /tmp/ros2.deb
    sudo apt-get update
    sudo apt-get install -y "ros-$ROS-ros-base"
fi

# dependencies the nodes need
source /opt/ros/*/setup.bash
sudo apt-get install -y "ros-$ROS_DISTRO-cv-bridge" python3-opencv python3-colcon-common-extensions

# build the package (algorithm.py is copied in so both this and demo.py share one file)
mkdir -p ~/ros2_ws/src
rm -rf ~/ros2_ws/src/pennair_ros2 ~/ros2_ws/build ~/ros2_ws/install ~/ros2_ws/log
cp -r "$HERE/pennair_ros2" ~/ros2_ws/src/
cp "$HERE/algorithm.py" ~/ros2_ws/src/pennair_ros2/pennair_ros2/
cd ~/ros2_ws
colcon build --packages-select pennair_ros2
source install/setup.bash

[ -n "$VIDEO" ] && exec ros2 launch pennair_ros2 pennair.launch.py video:="$VIDEO"
