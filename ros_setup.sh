#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "/opt/ros/humble/setup.bash" ]; then
    source /opt/ros/humble/setup.bash
fi

export ROS_DOMAIN_ID=42

if [ -f "$SCRIPT_DIR/ros2_ws/install/local_setup.bash" ]; then
    source "$SCRIPT_DIR/ros2_ws/install/local_setup.bash"
    echo "Sourced ros2_ws/install/local_setup.bash (ROS_DOMAIN_ID=$ROS_DOMAIN_ID)"
else
    echo "Workspace not built yet. Build with: (cd \"$SCRIPT_DIR/ros2_ws\" && colcon build --symlink-install)"
fi
