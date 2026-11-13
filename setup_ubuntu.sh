#!/usr/bin/env bash
# ==============================================================================
# setup_ubuntu.sh - 1-Click Out-of-the-Box Setup for Ubuntu 22.04 / 24.04
# Automatically sets up ROS 2 Humble, Godot 4, python dependencies, and builds
# both the ROS 2 workspace and the ros2_for_godot GDExtension bridge.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "====================================================================="
echo "  Underwater Robotics 2026-2027: Ubuntu Out-of-the-Box Setup"
echo "====================================================================="

# 1. Verify OS is Ubuntu / Debian
if [ ! -f /etc/os-release ]; then
    echo "Error: This script is intended for Ubuntu Linux."
    exit 1
fi
source /etc/os-release
echo "Detected OS: $NAME $VERSION"

# 2. Install base system dependencies
echo ""
echo ">>> Step 1/6: Installing core build tools and dependencies..."
sudo apt update
sudo apt install -y \
    software-properties-common \
    curl \
    gnupg \
    lsb-release \
    git \
    cmake \
    g++ \
    build-essential \
    unzip \
    python3-pip \
    python3-colcon-common-extensions \
    python3-pygame \
    python3-serial \
    python3-numpy

# 3. Check and install ROS 2 Humble
echo ""
echo ">>> Step 2/6: Checking ROS 2 Humble..."
if [ ! -f "/opt/ros/humble/setup.bash" ]; then
    echo "ROS 2 Humble not found. Installing from official ROS 2 repository..."
    sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
    sudo apt update
    sudo apt install -y \
        ros-humble-ros-base \
        ros-humble-joy \
        ros-humble-image-transport \
        ros-humble-cv-bridge
else
    echo "ROS 2 Humble already installed at /opt/ros/humble."
fi

source /opt/ros/humble/setup.bash

# 4. Check and install Godot 4
echo ""
echo ">>> Step 3/6: Checking Godot 4..."
if ! command -v godot &>/dev/null && ! command -v godot4 &>/dev/null; then
    echo "Godot 4 not found. Downloading official Godot 4 binary..."
    ARCH="$(uname -m)"
    if [ "$ARCH" = "x86_64" ]; then
        GODOT_ZIP="Godot_v4.3-stable_linux.x86_64.zip"
        GODOT_BIN_NAME="Godot_v4.3-stable_linux.x86_64"
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
        GODOT_ZIP="Godot_v4.3-stable_linux.arm64.zip"
        GODOT_BIN_NAME="Godot_v4.3-stable_linux.arm64"
    fi

    DOWNLOAD_URL="https://github.com/godotengine/godot/releases/download/4.3-stable/${GODOT_ZIP}"
    echo "Downloading $DOWNLOAD_URL ..."
    curl -L "$DOWNLOAD_URL" -o "/tmp/${GODOT_ZIP}"
    unzip -q -o "/tmp/${GODOT_ZIP}" -d /tmp/
    sudo mv "/tmp/${GODOT_BIN_NAME}" /usr/local/bin/godot
    sudo chmod +x /usr/local/bin/godot
    rm -f "/tmp/${GODOT_ZIP}"
    echo "Installed Godot 4 to /usr/local/bin/godot"
else
    echo "Godot is already installed: $(command -v godot || command -v godot4)"
fi

# 5. Initialize git submodules
echo ""
echo ">>> Step 4/6: Initializing git submodules (godot-cpp)..."
git submodule update --init --recursive

# 6. Build ROS 2 workspace (rov_ctrl_sys)
echo ""
echo ">>> Step 5/6: Building local ROS 2 workspace..."
(
    cd "$SCRIPT_DIR/ros2_ws"
    colcon build --symlink-install
)
source "$SCRIPT_DIR/ros2_ws/install/local_setup.bash"

# 7. Build ros2_for_godot GDExtension
echo ""
echo ">>> Step 6/6: Compiling ros2_for_godot GDExtension bridge..."
ARCH="$(uname -m)"
(
    cd "$SCRIPT_DIR/underwater-robotics-groundstation/ros2-for-godot"
    cmake -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=/opt/ros/humble
    cmake --build build -j"$(nproc 2>/dev/null || echo 4)"
    mkdir -p "../addons/ros2_for_godot/bin/linux.${ARCH}"
    cp build/bin/libros2_for_godot.so "../addons/ros2_for_godot/bin/linux.${ARCH}/libros2_for_godot.so"
)

echo ""
echo "====================================================================="
echo "  Setup Complete! System is ready to run out of the box."
echo "====================================================================="
echo ""
echo "To run the 3D Godot Simulation & Groundstation UI:"
echo "  ./run_groundstation.sh"
echo ""
echo "To run the full ROS 2 Python Simulation + Groundstation UI:"
echo "  ./run_sim.sh"
echo ""
