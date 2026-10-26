# ros2-for-godot

GDExtension plugin that integrates ROS 2 into Godot Engine. Provides rclpy-like API in GDScript with native C++ performance via rclcpp.
https://github.com/Kotakku/ros2-for-godot/tree/main
## Features

- **GDExtension (C++)** — no Godot engine rebuild required
- **Suppoerted message types** generated from std_msgs, geometry_msgs, sensor_msgs, nav_msgs, tf2_msgs, builtin_interfaces
- **QoS profiles** — full QoS configuration with rclpy-compatible presets

## Quick Start

```gdscript
extends RosNode

var pub: RosPublisher
var sub: RosSubscription

func _ready():
    ros_node_name = "my_node"
    await get_tree().process_frame

    pub = create_publisher("geometry_msgs/msg/Twist", "/cmd_vel", 10)
    sub = create_subscription("geometry_msgs/msg/Twist", "/cmd_vel", _on_twist, 10)

func _physics_process(_delta):
    spin_some()

    var msg = RosMsg.create("geometry_msgs/msg/Twist")
    msg.linear = Vector3(1.0, 0.0, 0.0)
    pub.publish(msg)

func _on_twist(msg):
    print("Received: ", msg.linear)
```

## Requirements

- **Godot** 4.5+ (tested with 4.7.1)
- **ROS 2 Jazzy** (other distros may work)
- **CMake** 3.16+
- **C++17** compiler

## Build

Two build modes are available, matching the ros2-for-unity approach:

| Mode | Description | ROS2 needed at runtime? |
|---|---|---|
| **Overlay** (default) | Links against local ROS2 installation | Yes |
| **Standalone** | Builds ROS2 from source, bundles all .so files | No |

```bash
# Clone with submodules
git clone --recursive <repo-url>
cd ros2-for-godot

# Checkout godot-cpp matching your Godot version
cd godot-cpp
git checkout godot-4.5-stable  # or the commit matching your Godot version
cd ..
```

### Overlay build

```bash
source /opt/ros/humble/setup.bash
./build.sh                  # Release (default)
./build.sh --overlay Debug  # Debug build
```

### Standalone build

Builds ROS2 dependencies from source via `vcs import` + `colcon build`, then bundles all .so files. Requires: `vcs`, `colcon`, `patchelf`.

```bash
pip3 install vcstool colcon-common-extensions
sudo apt install patchelf

./build.sh --standalone
```

The built libraries are at `build/bin/`.

### Install into Godot project

```bash
./create_addon.sh
# -> build/ros2_for_godot.zip

unzip build/ros2_for_godot.zip -d /path/to/your-godot-project/addons/
```

```
your-godot-project/
└── addons/
    └── ros2_for_godot/
        ├── ros2_for_godot.gdextension
        └── bin/
            ├── libros2_for_godot.so
            └── (standalone: additional ROS2 .so files)
```

For **overlay** builds, launch Godot with ROS2 sourced:
```bash
source /opt/ros/humble/setup.bash
godot --editor
```

For **standalone** builds, Godot can be launched directly without ROS2.

## API Reference

### RosNode

Extend `RosNode` to create a GDScript node with ROS 2 capabilities.

| Method | Description |
|---|---|
| `create_publisher(type_name, topic, qos)` | Create a publisher. `qos`: int (depth) or `RosQoSProfile` |
| `create_subscription(type_name, topic, callback, qos)` | Create a subscription |
| `spin_some()` | Process pending callbacks. Call in `_physics_process()` |
| `now()` | Current ROS clock time in seconds |

**Properties:** `ros_node_name`, `ros_namespace`

### RosMsg

Factory for creating message instances.

```gdscript
var msg = RosMsg.create("sensor_msgs/msg/Image")
msg.width = 640
msg.height = 480
```

### RosQoSProfile

QoS configuration. Accepts enum constants or presets.

```gdscript
# Presets (rclpy-compatible)
var qos = RosQoSProfile.sensor_data()   # BEST_EFFORT, depth=5
var qos = RosQoSProfile.services()      # RELIABLE, depth=10

# Custom
var qos = RosQoSProfile.new()
qos.reliability = RosQoSProfile.BEST_EFFORT
qos.durability = RosQoSProfile.TRANSIENT_LOCAL
qos.depth = 1
```

**Presets:** `preset_default()`, `sensor_data()`, `services()`, `parameters()`, `parameter_events()`, `best_effort(depth)`

**Enums:** `RELIABLE`, `BEST_EFFORT`, `VOLATILE`, `TRANSIENT_LOCAL`, `KEEP_LAST`, `KEEP_ALL`, `AUTOMATIC`, `MANUAL_BY_TOPIC`

### Supported message types

- **std_msgs** — Bool, Byte, String, Int32, Float64, Header, ColorRGBA, ...
- **geometry_msgs** — Twist, Pose, PoseStamped, Transform, TransformStamped, Odometry, Quaternion, Vector3, Wrench, ...
- **sensor_msgs** — Image, LaserScan, PointCloud2, Imu, CameraInfo, CompressedImage, JointState, ...
- **nav_msgs** — Odometry, Path, OccupancyGrid, MapMetaData, ...
- **tf2_msgs** — TFMessage, TF2Error
- **builtin_interfaces** — Time, Duration

## Adding custom message packages

Pass additional packages via the `GEN_PACKAGES` CMake variable:

```bash
source /opt/ros/humble/setup.bash
cd build
cmake .. -DGEN_PACKAGES="std_msgs;geometry_msgs;sensor_msgs;nav_msgs;tf2_msgs;custom_msgs"
cmake --build . -j$(nproc)
```

The generator runs automatically at configure time, reads `.msg` files from the ROS 2 install directory, and produces GDExtension C++ classes with bridge code into `build/gen/`.
