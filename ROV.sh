#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE_PID=""
LOCAL_PID=""

graceful_stop() {
    local pid="$1"
    local name="$2"

    [[ -z "$pid" ]] && return

    echo "Stopping $name gracefully..."
    kill -INT "$pid" 2>/dev/null

    sleep 3

    if kill -0 "$pid" 2>/dev/null; then
        echo "$name did not exit; killing..."
        kill -TERM "$pid" 2>/dev/null
        sleep 10
    fi

    if kill -0 "$pid" 2>/dev/null; then
        echo "$name still alive; force killing..."
        kill -KILL "$pid" 2>/dev/null
    fi
}

cleanup() {
    echo "Cleaning up..."

    graceful_stop "$REMOTE_PID" "remote launch"
    graceful_stop "$LOCAL_PID" "local launch"
}

trap cleanup EXIT INT TERM

run_in_term() {
    local title="$1"
    local cmd="$2"

    if command -v xterm &>/dev/null; then
        xterm -T "$title" -e bash -lc "$cmd" &
    elif command -v gnome-terminal &>/dev/null; then
        gnome-terminal --title="$title" -- bash -lc "$cmd" &
    elif command -v konsole &>/dev/null; then
        konsole --title "$title" -e bash -lc "$cmd" &
    else
        bash -lc "$cmd" &
    fi
}

run_in_term "ROV Remote Launch" "
ssh -t ROV '
if [ -f ~/Underwater-Robotics-26-27/ros_setup.sh ]; then
    source ~/Underwater-Robotics-26-27/ros_setup.sh
elif [ -f ~/Underwater-Robotics-Current/ros_setup.sh ]; then
    source ~/Underwater-Robotics-Current/ros_setup.sh
fi
ros2 launch rov_ctrl_sys launch_rov.launch.py
'
"
REMOTE_PID=$!

sleep 1

run_in_term "ROV Local Launch" "
source \"$SCRIPT_DIR/ros_setup.sh\"
ros2 launch rov_ctrl_sys launch_ground.launch.py
"
LOCAL_PID=$!

wait -n "$REMOTE_PID" "$LOCAL_PID"
