#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
BUILD_TYPE="Release"
BUILD_MODE="overlay"
CLEAN_INSTALL=0

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        -s|--standalone)  BUILD_MODE="standalone"; shift ;;
        -o|--overlay)     BUILD_MODE="overlay"; shift ;;
        -c|--clean-install)
            CLEAN_INSTALL=1; shift ;;
        Debug|Release|RelWithDebInfo)
            BUILD_TYPE="$1"; shift ;;
        -h|--help)
            echo "Usage: $0 [--overlay|--standalone] [--clean-install] [Debug|Release]"
            echo ""
            echo "Options:"
            echo "  --overlay     (default) Link against local ROS2 installation"
            echo "  --standalone  Build ROS2 from source and bundle all libraries"
            echo "  --clean-install  Remove build directory before building"
            echo "  Debug/Release    Build type (default: Release)"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# --- Clean ---
if [ "${CLEAN_INSTALL}" = "1" ]; then
    echo "Cleaning build directory..."
    rm -rf "${BUILD_DIR}"
fi

echo "=== ros2-for-godot build ==="
echo "Mode: ${BUILD_MODE}"
echo "Build type: ${BUILD_TYPE}"

# --- Overlay build ---
build_overlay() {
    if [ -z "$AMENT_PREFIX_PATH" ]; then
        echo "Error: ROS2 environment not sourced. Run: source /opt/ros/<distro>/setup.bash"
        exit 1
    fi
    echo "ROS2: ${AMENT_PREFIX_PATH}"

    mkdir -p "${BUILD_DIR}"
    cd "${BUILD_DIR}"
    cmake "${SCRIPT_DIR}" -DCMAKE_BUILD_TYPE="${BUILD_TYPE}"
    cmake --build . -j"$(nproc)"

    echo ""
    echo "=== Build complete (overlay) ==="
    echo "Library: ${BUILD_DIR}/bin/libros2_for_godot.so"
    echo "Note: ROS2 must be sourced before running Godot."
}

# --- Standalone build ---
build_standalone() {
    local ROS2_WS="${BUILD_DIR}/ros2_ws"
    local ROS2_SRC="${ROS2_WS}/src"
    local ROS2_INSTALL="${ROS2_WS}/install"
    local GD_BUILD="${BUILD_DIR}/gdext"
    local LIB_DIR="${BUILD_DIR}/bin"

    # Check required tools
    for cmd in vcs colcon patchelf; do
        if ! command -v "$cmd" &>/dev/null; then
            echo "Error: '${cmd}' not found."
            echo "Install with: pip3 install vcstool colcon-common-extensions && sudo apt install patchelf"
            exit 1
        fi
    done

    # Detect ROS2 distro for repos file
    local ROS_DISTRO="${ROS_DISTRO:-humble}"
    local REPOS_FILE="${SCRIPT_DIR}/ros2_standalone_${ROS_DISTRO}.repos"
    if [ ! -f "${REPOS_FILE}" ]; then
        echo "Error: Repos file not found: ${REPOS_FILE}"
        echo "Supported distros: $(ls "${SCRIPT_DIR}"/ros2_standalone_*.repos 2>/dev/null | sed 's/.*ros2_standalone_//;s/\.repos//' | tr '\n' ' ')"
        exit 1
    fi

    # Step 1: Import ROS2 sources
    echo ""
    echo "--- Step 1/4: Importing ROS2 sources (${ROS_DISTRO}) ---"
    if [ ! -d "${ROS2_SRC}" ]; then
        mkdir -p "${ROS2_SRC}"
        vcs import "${ROS2_SRC}" < "${REPOS_FILE}"
    else
        echo "  Sources already exist. To re-import, delete ${ROS2_SRC}"
    fi

    # Step 2: Build ROS2 with colcon
    echo ""
    echo "--- Step 2/4: Building ROS2 packages ---"
    if [ ! -f "${ROS2_INSTALL}/setup.bash" ]; then
        cd "${ROS2_WS}"

        # colcon needs at least cmake and python3
        colcon build \
            --merge-install \
            --cmake-args \
                -DCMAKE_BUILD_TYPE=Release \
                -DBUILD_TESTING=OFF \
                -Wno-dev \
            --packages-up-to \
                rclcpp \
                std_msgs geometry_msgs sensor_msgs nav_msgs tf2_msgs \
                rmw_cyclonedds_cpp \
                rosidl_typesupport_fastrtps_cpp rosidl_typesupport_fastrtps_c \
                rosidl_typesupport_introspection_cpp rosidl_typesupport_introspection_c \
            --packages-ignore \
                test_msgs
    else
        echo "  ROS2 install already exists. To rebuild, delete ${ROS2_INSTALL}"
    fi

    # Step 3: Build GDExtension against local ROS2
    echo ""
    echo "--- Step 3/4: Building GDExtension ---"
    source "${ROS2_INSTALL}/setup.bash"

    mkdir -p "${GD_BUILD}"
    cd "${GD_BUILD}"
    cmake "${SCRIPT_DIR}" -DCMAKE_BUILD_TYPE="${BUILD_TYPE}"
    cmake --build . -j"$(nproc)"

    # Step 4: Collect all .so dependencies into bin/
    echo ""
    echo "--- Step 4/4: Collecting standalone libraries ---"
    mkdir -p "${LIB_DIR}"
    cp "${GD_BUILD}/bin/libros2_for_godot.so" "${LIB_DIR}/"

    python3 "${SCRIPT_DIR}/scripts/collect_libs.py" \
        "${LIB_DIR}/libros2_for_godot.so" \
        "${ROS2_INSTALL}" \
        "${LIB_DIR}"

    # Set RPATH so all .so files find each other via $ORIGIN
    echo "  Setting RPATH..."
    for so in "${LIB_DIR}"/*.so*; do
        patchelf --set-rpath '$ORIGIN' "$so" 2>/dev/null || true
    done

    local so_count
    so_count=$(find "${LIB_DIR}" -name "*.so*" | wc -l)

    echo ""
    echo "=== Build complete (standalone) ==="
    echo "Libraries: ${LIB_DIR}/"
    echo "${so_count} .so files collected"
    echo "No ROS2 installation required at runtime."
}

# --- Dispatch ---
if [ "${BUILD_MODE}" = "standalone" ]; then
    build_standalone
else
    build_overlay
fi
