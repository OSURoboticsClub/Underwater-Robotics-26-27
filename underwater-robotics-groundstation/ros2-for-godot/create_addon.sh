#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ADDON_NAME="ros2_for_godot"
ADDON_DIR="${SCRIPT_DIR}/build/addon/${ADDON_NAME}"
ZIP_PATH="${SCRIPT_DIR}/build/${ADDON_NAME}.zip"
LIB_DIR="${SCRIPT_DIR}/build/bin"

# Select the library architecture from the current build host.
case "$(uname -m)" in
    x86_64) GODOT_ARCH="x86_64" ;;
    aarch64|arm64) GODOT_ARCH="arm64" ;;
    *)
        echo "Error: Unsupported Linux architecture: $(uname -m)"
        exit 1
        ;;
esac

# Check that the library exists
if [ ! -f "${LIB_DIR}/libros2_for_godot.so" ]; then
    echo "Error: Library not found. Run ./build.sh first."
    exit 1
fi

echo "=== Creating addon package ==="

# Clean and create addon directory
rm -rf "${SCRIPT_DIR}/build/addon"
mkdir -p "${ADDON_DIR}/bin"

# Copy all .so files (main lib + standalone deps if present)
cp "${LIB_DIR}"/*.so* "${ADDON_DIR}/bin/" 2>/dev/null || true

# Preserve symlinks in zip
local_count=$(find "${ADDON_DIR}/bin" -name "*.so*" | wc -l)
echo "  ${local_count} library files"

# Write .gdextension
cat > "${ADDON_DIR}/${ADDON_NAME}.gdextension" <<EOF
[configuration]

entry_symbol = "ros2_for_godot_init"
compatibility_minimum = "4.2"

[libraries]

linux.debug.${GODOT_ARCH} = "res://addons/ros2_for_godot/bin/libros2_for_godot.so"
linux.release.${GODOT_ARCH} = "res://addons/ros2_for_godot/bin/libros2_for_godot.so"
EOF

# Create zip
rm -f "${ZIP_PATH}"
cd "${SCRIPT_DIR}/build/addon"
zip -ry "${ZIP_PATH}" "${ADDON_NAME}/"

echo ""
echo "=== Addon package created ==="
echo "ZIP: ${ZIP_PATH}"
echo ""
echo "Install: unzip into your Godot project root:"
echo "  unzip ${ZIP_PATH} -d /path/to/your-project/addons/"
