#!/usr/bin/env zsh

SCRIPT_DIR="${0:A:h}"

# Activate conda environment if not already active
if [[ "$CONDA_DEFAULT_ENV" != "rov-humble" ]]; then
    if ! command -v conda &>/dev/null; then
        for cpath in \
            "$HOME/miniforge3/etc/profile.d/conda.sh" \
            "$HOME/miniconda3/etc/profile.d/conda.sh" \
            "$HOME/anaconda3/etc/profile.d/conda.sh" \
            "/opt/anaconda3/etc/profile.d/conda.sh" \
            "/opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh" \
            "/usr/local/Caskroom/miniforge/base/etc/profile.d/conda.sh"; do
            if [[ -f "$cpath" ]]; then
                source "$cpath"
                break
            fi
        done
    fi
    if command -v conda &>/dev/null; then
        echo "Activating rov-humble conda environment..."
        conda activate rov-humble
    fi
fi

export ROS_DOMAIN_ID=42

# Source local workspace build if it exists
if [[ -f "$SCRIPT_DIR/ros2_ws/install/local_setup.zsh" ]]; then
    source "$SCRIPT_DIR/ros2_ws/install/local_setup.zsh"
    echo "Sourced ros2_ws/install/local_setup.zsh (ROS_DOMAIN_ID=$ROS_DOMAIN_ID)"
else
    echo "Workspace not built yet. Build with: (cd \"$SCRIPT_DIR/ros2_ws\" && colcon build --symlink-install)"
fi
