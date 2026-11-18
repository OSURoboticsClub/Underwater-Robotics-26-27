#!/usr/bin/env bash
# ==============================================================================
# setup_ubuntu.sh - 1-Click Out-of-the-Box Setup for Ubuntu Linux
# Supports Ubuntu 22.04 LTS (native apt) and Ubuntu 24.04 LTS (Robostack / Conda)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "====================================================================="
echo "  Underwater Robotics 2026-2027: Ubuntu Setup"
echo "====================================================================="

# 1. Verify OS
if [ ! -f /etc/os-release ]; then
    echo "Error: /etc/os-release not found. This script requires Ubuntu Linux."
    exit 1
fi
source /etc/os-release
echo "Detected OS: $NAME $VERSION ($VERSION_CODENAME)"

# 2. Base build tools & Python headers
echo ""
echo ">>> Step 1/6: Installing build essentials and system packages..."
sudo apt update
sudo apt install -y software-properties-common curl gnupg lsb-release
sudo add-apt-repository -y universe
sudo apt update
sudo apt install -y \
    curl \
    gnupg \
    lsb-release \
    git \
    cmake \
    g++ \
    build-essential \
    pkg-config \
    unzip \
    xterm \
    python3 \
    python3-dev \
    libpython3-dev \
    python3-pip \
    python3-setuptools \
    python3-pygame \
    python3-serial \
    python3-numpy \
    python3-colcon-common-extensions

# 3. ROS 2 Humble Installation
echo ""
echo ">>> Step 2/6: Configuring ROS 2 Humble..."

if [ "$VERSION_CODENAME" = "jammy" ] || [ "$VERSION_ID" = "22.04" ]; then
    # Ubuntu 22.04 LTS: Use official OSRF APT repository
    if [ ! -f "/opt/ros/humble/setup.bash" ]; then
        echo "Installing ROS 2 Humble from official APT repository..."
        sudo mkdir -p /usr/share/keyrings
        sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu jammy main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
        sudo apt update
        sudo apt install -y \
            ros-humble-ros-base \
            ros-humble-nav-msgs \
            ros-humble-tf2-msgs \
            ros-humble-sensor-msgs \
            ros-humble-geometry-msgs \
            ros-humble-std-msgs \
            ros-humble-joy \
            ros-humble-image-transport \
            ros-humble-cv-bridge \
            ros-humble-usb-cam 2>/dev/null || true
    else
        echo "Found existing ROS 2 Humble at /opt/ros/humble."
        # Ensure message packages are installed
        sudo apt install -y \
            ros-humble-nav-msgs \
            ros-humble-tf2-msgs \
            ros-humble-sensor-msgs \
            ros-humble-geometry-msgs \
            ros-humble-std-msgs \
            ros-humble-joy \
            ros-humble-image-transport \
            ros-humble-cv-bridge \
            ros-humble-usb-cam 2>/dev/null || true
    fi
    source /opt/ros/humble/setup.bash
else
    # Ubuntu 24.04 (Noble) or other distributions:
    # Official ROS 2 Humble debs only exist for 22.04. On 24.04, install via Robostack/Conda.
    echo "Ubuntu 24.04 / non-22.04 detected. Setting up ROS 2 Humble via Robostack/Conda..."
    if ! command -v conda &>/dev/null; then
        echo "Installing Miniforge (Conda package manager)..."
        MINIFORGE_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-$(uname -m).sh"
        curl -fsSL "$MINIFORGE_URL" -o /tmp/miniforge.sh
        bash /tmp/miniforge.sh -b -p "$HOME/miniforge3"
        rm -f /tmp/miniforge.sh
        source "$HOME/miniforge3/etc/profile.d/conda.sh"
    else
        eval "$(conda shell.bash hook)"
    fi

    if ! conda info --envs | grep -q "rov-humble"; then
        echo "Creating rov-humble Conda environment from environment.yaml..."
        conda env create -f "$SCRIPT_DIR/environment.yaml"
    fi
    conda activate rov-humble
fi

# 4. Godot 4 Installation
echo ""
echo ">>> Step 3/6: Checking Godot 4 executable..."
if ! command -v godot &>/dev/null && ! command -v godot4 &>/dev/null; then
    echo "Godot 4 not found in PATH. Downloading official Godot 4.3 executable..."
    ARCH="$(uname -m)"
    if [ "$ARCH" = "x86_64" ]; then
        GODOT_ZIP="Godot_v4.3-stable_linux.x86_64.zip"
        GODOT_BIN_NAME="Godot_v4.3-stable_linux.x86_64"
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
        GODOT_ZIP="Godot_v4.3-stable_linux.arm64.zip"
        GODOT_BIN_NAME="Godot_v4.3-stable_linux.arm64"
    fi

    DOWNLOAD_URL="https://github.com/godotengine/godot/releases/download/4.3-stable/${GODOT_ZIP}"
    echo "Downloading from: $DOWNLOAD_URL ..."
    curl -L "$DOWNLOAD_URL" -o "/tmp/${GODOT_ZIP}"
    unzip -q -o "/tmp/${GODOT_ZIP}" -d /tmp/
    sudo mv "/tmp/${GODOT_BIN_NAME}" /usr/local/bin/godot
    sudo chmod +x /usr/local/bin/godot
    rm -f "/tmp/${GODOT_ZIP}"
    echo "Installed Godot 4 to /usr/local/bin/godot"
else
    echo "Found Godot in PATH: $(command -v godot || command -v godot4)"
fi

# 5. Git Submodules (godot-cpp)
echo ""
echo ">>> Step 4/6: Initializing git submodules..."
git submodule update --init --recursive

# 6. Build ROS 2 workspace (rov_ctrl_sys)
echo ""
echo ">>> Step 5/6: Building local ROS 2 workspace..."
(
    cd "$SCRIPT_DIR/ros2_ws"
    colcon build --symlink-install
)
if [ -f "$SCRIPT_DIR/ros2_ws/install/local_setup.bash" ]; then
    source "$SCRIPT_DIR/ros2_ws/install/local_setup.bash"
fi

# 7. Compile ros2_for_godot GDExtension
echo ""
echo ">>> Step 6/6: Compiling ros2_for_godot GDExtension bridge..."
ARCH="$(uname -m)"
[ "$ARCH" = "aarch64" ] && ARCH="arm64"
PREFIX_PATH="${AMENT_PREFIX_PATH:-/opt/ros/humble}"

(
    cd "$SCRIPT_DIR/underwater-robotics-groundstation/ros2-for-godot"
    rm -rf build/CMakeCache.txt build/CMakeFiles 2>/dev/null || true
    cmake -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$PREFIX_PATH"
    cmake --build build -j"$(nproc 2>/dev/null || echo 4)"
    mkdir -p "../addons/ros2_for_godot/bin/linux.${ARCH}"
    cp build/bin/libros2_for_godot.so "../addons/ros2_for_godot/bin/linux.${ARCH}/libros2_for_godot.so"
    if [ "$ARCH" = "arm64" ]; then
        mkdir -p "../addons/ros2_for_godot/bin/linux.aarch64"
        cp build/bin/libros2_for_godot.so "../addons/ros2_for_godot/bin/linux.aarch64/libros2_for_godot.so"
    fi
)

TARGET_LIB="$SCRIPT_DIR/underwater-robotics-groundstation/addons/ros2_for_godot/bin/linux.${ARCH}/libros2_for_godot.so"
if [ ! -f "$TARGET_LIB" ]; then
    echo "ERROR: Compilation finished but $TARGET_LIB was not created."
    exit 1
fi
echo "Successfully compiled: $TARGET_LIB"

# 8. Verification test with Godot
echo ""
echo ">>> Importing Godot assets and verifying scene loading..."
GODOT_CMD="$(command -v godot || command -v godot4 || echo '/usr/local/bin/godot')"
"$GODOT_CMD" --headless --editor --quit --path "$SCRIPT_DIR/underwater-robotics-groundstation" || {
    echo "Warning: Godot headless verification exited with code $?."
}

echo ""
echo "====================================================================="
echo "  Setup Complete! System is ready to run on Ubuntu."
echo "====================================================================="
echo ""
echo "To run the 3D Godot Simulation & Groundstation UI:"
echo "  ./run_groundstation.sh"
echo ""
echo "To run the full ROS 2 Python Simulation + Groundstation UI:"
echo "  ./run_sim.sh"
echo ""
