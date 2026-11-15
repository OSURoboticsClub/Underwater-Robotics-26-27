#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "/opt/ros/humble/setup.bash" ]; then
    source /opt/ros/humble/setup.bash
elif [ -z "$ROS_DISTRO" ]; then
    for conda_sh in \
        "$HOME/miniforge3/etc/profile.d/conda.sh" \
        "$HOME/miniconda3/etc/profile.d/conda.sh" \
        "$HOME/anaconda3/etc/profile.d/conda.sh" \
        "/opt/anaconda3/etc/profile.d/conda.sh"; do
        if [ -f "$conda_sh" ]; then
            source "$conda_sh"
            conda activate rov-humble 2>/dev/null || true
            break
        fi
    done
fi

export ROS_DOMAIN_ID=42

if [ -f "$SCRIPT_DIR/ros2_ws/install/local_setup.bash" ]; then
    source "$SCRIPT_DIR/ros2_ws/install/local_setup.bash"
    echo "Sourced ros2_ws/install/local_setup.bash (ROS_DOMAIN_ID=$ROS_DOMAIN_ID)"
else
    echo "Workspace not built yet. Build with: (cd \"$SCRIPT_DIR/ros2_ws\" && colcon build --symlink-install)"
fi
