#!/usr/bin/env zsh

# Activate the conda environment if not already active
if [[ "$CONDA_DEFAULT_ENV" != "rov-humble" ]]; then
    echo "Activating rov-humble conda environment..."
    conda activate rov-humble
fi

export ROS_DOMAIN_ID=42

# Source local workspace build if it exists
if [[ -f "./ros2_ws/install/local_setup.zsh" ]]; then
    source ./ros2_ws/install/local_setup.zsh
    echo "Sourced ros2_ws/install/local_setup.zsh (ROS_DOMAIN_ID=$ROS_DOMAIN_ID)"
else
    echo "Workspace not built yet. Build with: (cd ros2_ws && colcon build --symlink-install)"
fi
