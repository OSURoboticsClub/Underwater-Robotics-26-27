#!/usr/bin/env bash
set -eo pipefail

GODOT_VERSION="4.7.1"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_DIR="$SCRIPT_DIR/underwater-robotics-groundstation"

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "This launcher currently supports Linux only." >&2
    exit 1
fi

case "$(uname -m)" in
    x86_64)
        GODOT_ARCH="x86_64"
        ;;
    aarch64|arm64)
        GODOT_ARCH="arm64"
        ;;
    *)
        echo "Unsupported CPU architecture: $(uname -m)" >&2
        exit 1
        ;;
esac

GODOT_BINARY="Godot_v${GODOT_VERSION}-stable_linux.${GODOT_ARCH}"

has_required_version() {
    local version_output
    [[ -x "$1" ]] || return 1
    version_output="$("$1" --version 2>/dev/null)" || return 1
    [[ "$version_output" == "$GODOT_VERSION"* && "$version_output" != *mono* ]]
}

godot_path=""
if command -v godot >/dev/null 2>&1 && has_required_version "$(command -v godot)"; then
    godot_path="$(command -v godot)"
fi

if [[ -z "$godot_path" ]]; then
    found_godot="$(find "$HOME" -type f -name "$GODOT_BINARY" -perm /111 -print -quit)"
    if [[ -n "$found_godot" ]] && has_required_version "$found_godot"; then
        godot_path="$found_godot"
    fi
fi

if [[ -z "$godot_path" ]]; then
    if ! command -v curl >/dev/null 2>&1 || ! command -v unzip >/dev/null 2>&1; then
        echo "Both curl and unzip are required to download Godot." >&2
        exit 1
    fi

    install_dir="$HOME/.local/share/godot/$GODOT_VERSION"
    mkdir -p "$install_dir"
    temp_dir="$(mktemp -d "$install_dir/.download.XXXXXX")"
    trap 'rm -rf -- "$temp_dir"' EXIT

    download_url="https://github.com/godotengine/godot/releases/download/${GODOT_VERSION}-stable/${GODOT_BINARY}.zip"
    echo "Downloading Godot ${GODOT_VERSION} for ${GODOT_ARCH}..."
    curl --fail --location --retry 3 --output "$temp_dir/godot.zip" "$download_url"
    unzip -q "$temp_dir/godot.zip" -d "$temp_dir"

    downloaded_godot="$temp_dir/$GODOT_BINARY"
    if [[ ! -f "$downloaded_godot" ]]; then
        echo "The downloaded archive did not contain $GODOT_BINARY." >&2
        exit 1
    fi
    chmod +x "$downloaded_godot"
    if ! has_required_version "$downloaded_godot"; then
        echo "The downloaded Godot binary did not report version ${GODOT_VERSION}." >&2
        exit 1
    fi

    godot_path="$install_dir/$GODOT_BINARY"
    mv -f -- "$downloaded_godot" "$godot_path"
    rm -rf -- "$temp_dir"
    trap - EXIT
fi

if [[ ! -d "$PROJECT_DIR" ]]; then
    echo "Godot project directory not found: $PROJECT_DIR" >&2
    exit 1
fi

if [[ ! -r "$SCRIPT_DIR/ros_setup.sh" ]]; then
    echo "ROS setup script not found or unreadable: $SCRIPT_DIR/ros_setup.sh" >&2
    exit 1
fi

source "$SCRIPT_DIR/ros_setup.sh"

force_software_rendering="${GODOT_FORCE_SOFTWARE_RENDERING:-0}"
case "$force_software_rendering" in
    1)
        use_software_rendering=true
        ;;
    0)
        use_software_rendering=false
        ;;
    auto)
        use_software_rendering=false
        if command -v glxinfo >/dev/null 2>&1 && glxinfo -B 2>/dev/null | grep -qi 'virgl'; then
            use_software_rendering=true
        fi
        ;;
    *)
        echo "GODOT_FORCE_SOFTWARE_RENDERING must be 'auto', '1', or '0'." >&2
        exit 1
        ;;
esac

if [[ "$use_software_rendering" == true ]]; then
    echo "Detected/selected software rendering (llvmpipe); Godot may run slower." >&2
    export LIBGL_ALWAYS_SOFTWARE=1
    export GALLIUM_DRIVER=llvmpipe
fi

exec "$godot_path" --path "$PROJECT_DIR" --editor
