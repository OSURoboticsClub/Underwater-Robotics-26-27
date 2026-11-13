#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GODOT_BIN="/Users/scuvyking/Downloads/Godot.app/Contents/MacOS/Godot"

if [ ! -f "$GODOT_BIN" ]; then
    echo "Error: Godot executable not found at $GODOT_BIN"
    exit 1
fi

"$GODOT_BIN" --path "$SCRIPT_DIR/underwater-robotics-groundstation" "$@"
