#!/bin/bash

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

xterm -T "ROV Remote Launch" -e bash -lc "
ssh -t ROV '
source ~/Underwater-Robotics-Current/ros_setup.sh
ros2 launch rov_ctrl_sys launch_rov.launch.py
'
" &
REMOTE_PID=$!

sleep 1

xterm -T "ROV Local Launch" -e bash -lc '
source ~/Underwater-Robotics-Current/ros_setup.sh
ros2 launch rov_ctrl_sys launch_ground.launch.py
' &
LOCAL_PID=$!

wait -n "$REMOTE_PID" "$LOCAL_PID"
