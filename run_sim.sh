#!/usr/bin/env bash
# ==============================================================================
# run_sim.sh - Run Underwater ROV Simulator + Groundstation UI locally on Mac
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Initialize conda
if [ -f "/opt/anaconda3/etc/profile.d/conda.sh" ]; then
    source "/opt/anaconda3/etc/profile.d/conda.sh"
    conda activate rov-humble
elif command -v conda &>/dev/null; then
    eval "$(conda shell.bash hook)"
    conda activate rov-humble
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
