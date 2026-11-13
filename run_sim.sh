#!/usr/bin/env bash
# ==============================================================================
# run_sim.sh - Run Underwater ROV Simulator + Groundstation UI locally
# Works portably across macOS and Linux without hardcoded user paths
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Detect and activate ROS 2 / Conda environment
if [ -n "$ROS_DISTRO" ]; then
    echo "Using active ROS 2 ($ROS_DISTRO) environment."
elif [ -f "/opt/ros/humble/setup.bash" ]; then
    echo "Found native ROS 2 Humble at /opt/ros/humble..."
    source "/opt/ros/humble/setup.bash"
else
    # Search common Conda installation paths if not in PATH
    if ! command -v conda &>/dev/null; then
        for conda_sh in \
            "$HOME/miniforge3/etc/profile.d/conda.sh" \
            "$HOME/miniconda3/etc/profile.d/conda.sh" \
            "$HOME/anaconda3/etc/profile.d/conda.sh" \
            "/opt/anaconda3/etc/profile.d/conda.sh" \
            "/opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh" \
            "/usr/local/Caskroom/miniforge/base/etc/profile.d/conda.sh"; do
            if [ -f "$conda_sh" ]; then
                source "$conda_sh"
                break
            fi
        done
    fi

    if command -v conda &>/dev/null; then
        eval "$(conda shell.bash hook)" 2>/dev/null || true
        conda activate rov-humble 2>/dev/null || true
    fi
fi

if ! command -v ros2 &>/dev/null; then
    echo "Error: 'ros2' command not found."
    echo "Please activate your ROS 2 environment or Conda 'rov-humble' environment before running."
    exit 1
fi

# 2. Source ROS 2 workspace environment
export ROS_DOMAIN_ID=42
if [ -f "$SCRIPT_DIR/ros2_ws/install/local_setup.bash" ]; then
    source "$SCRIPT_DIR/ros2_ws/install/local_setup.bash"
else
    echo "Building workspace first..."
    (cd "$SCRIPT_DIR/ros2_ws" && colcon build --symlink-install)
    source "$SCRIPT_DIR/ros2_ws/install/local_setup.bash"
fi

SIM_PID=""

cleanup() {
    echo ""
    echo "Shutting down underwater simulator..."
    if [ -n "$SIM_PID" ]; then
        kill -INT "$SIM_PID" 2>/dev/null
        wait "$SIM_PID" 2>/dev/null
    fi
    echo "Done."
}

trap cleanup EXIT INT TERM

# 3. Start Underwater Simulator nodes in background
echo "Starting Underwater 3D Simulator (ROS 2)..."
ros2 launch rov_ctrl_sys sim.launch.py &
SIM_PID=$!

# Wait briefly for ROS 2 nodes to initialize
sleep 2

# 4. Launch Godot Groundstation UI in foreground
echo "Launching Groundstation UI..."
"$SCRIPT_DIR/run_groundstation.sh"

echo "Groundstation closed."
