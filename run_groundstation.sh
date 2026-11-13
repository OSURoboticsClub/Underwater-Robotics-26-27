#!/usr/bin/env bash
# ==============================================================================
# run_groundstation.sh - Launch Godot Groundstation UI Portably
# Supports macOS (Apple Silicon / Intel) and Ubuntu/Linux
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Environment Detection & Library Paths (for ROS 2 / GDExtension bridge)
if [ -z "$CONDA_DEFAULT_ENV" ] && [ -z "$ROS_DISTRO" ]; then
    # Auto-detect Conda if installed in common user/system directories
    for conda_sh in \
        "$HOME/miniforge3/etc/profile.d/conda.sh" \
        "$HOME/miniconda3/etc/profile.d/conda.sh" \
        "$HOME/anaconda3/etc/profile.d/conda.sh" \
        "/opt/anaconda3/etc/profile.d/conda.sh" \
        "/opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh" \
        "/usr/local/Caskroom/miniforge/base/etc/profile.d/conda.sh"; do
        if [ -f "$conda_sh" ]; then
            source "$conda_sh"
            conda activate rov-humble 2>/dev/null || true
            break
        fi
    done

    # If on native Linux and not using conda, source ROS 2 Humble
    if [ -z "$ROS_DISTRO" ] && [ -f "/opt/ros/humble/setup.bash" ]; then
        source "/opt/ros/humble/setup.bash"
    fi
fi

# Ensure dynamic linker finds ROS 2 libraries
if [ -n "$CONDA_PREFIX" ]; then
    export DYLD_FALLBACK_LIBRARY_PATH="$CONDA_PREFIX/lib${DYLD_FALLBACK_LIBRARY_PATH:+:$DYLD_FALLBACK_LIBRARY_PATH}"
    export LD_LIBRARY_PATH="$CONDA_PREFIX/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
elif [ -n "$AMENT_PREFIX_PATH" ]; then
    export LD_LIBRARY_PATH="/opt/ros/humble/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi

# 2. Locate Godot Executable
find_godot() {
    # Check explicitly set environment variable
    if [ -n "$GODOT_BIN" ] && [ -x "$GODOT_BIN" ]; then
        echo "$GODOT_BIN"
        return 0
    fi

    # Check PATH
    for cmd in godot godot4 godot-engine; do
        if command -v "$cmd" &>/dev/null; then
            command -v "$cmd"
            return 0
        fi
    done

    # macOS specific search
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Check standard Applications directories
        for app in \
            "/Applications/Godot.app/Contents/MacOS/Godot" \
            "/Applications/Godot_mono.app/Contents/MacOS/Godot" \
            "$HOME/Applications/Godot.app/Contents/MacOS/Godot" \
            "$HOME/Downloads/Godot.app/Contents/MacOS/Godot"; do
            if [ -x "$app" ]; then
                echo "$app"
                return 0
            fi
        done

        # Query macOS Spotlight for any installed Godot.app
        local spotlight_app
        spotlight_app="$(mdfind "kMDItemCFBundleIdentifier == 'org.godotengine.godot'" 2>/dev/null | head -n 1)"
        if [ -n "$spotlight_app" ] && [ -x "$spotlight_app/Contents/MacOS/Godot" ]; then
            echo "$spotlight_app/Contents/MacOS/Godot"
            return 0
        fi
    fi

    # Linux specific search
    for bin_path in \
        "/usr/bin/godot" \
        "/usr/local/bin/godot" \
        "/snap/bin/godot" \
        "$HOME/.local/bin/godot"; do
        if [ -x "$bin_path" ]; then
            echo "$bin_path"
            return 0
        fi
    done

    return 1
}

GODOT_EXEC="$(find_godot)"

if [ -z "$GODOT_EXEC" ] || [ ! -x "$GODOT_EXEC" ]; then
    echo "================================================================="
    echo "Error: Godot 4 executable could not be found automatically."
    echo ""
    echo "Please do one of the following:"
    echo "  1. Set the GODOT_BIN environment variable:"
    echo "     export GODOT_BIN=/path/to/Godot"
    echo "     ./run_groundstation.sh"
    echo ""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  2. On macOS with Homebrew:"
        echo "     brew install --cask godot"
        echo "  3. Download Godot 4 from https://godotengine.org/download"
        echo "     and move it to /Applications"
    else
        echo "  2. On Ubuntu / Debian:"
        echo "     sudo apt install godot4"
        echo "  3. Download Godot 4 from https://godotengine.org/download"
    fi
    echo "================================================================="
    exit 1
fi

exec "$GODOT_EXEC" --path "$SCRIPT_DIR/underwater-robotics-groundstation" "$@"
