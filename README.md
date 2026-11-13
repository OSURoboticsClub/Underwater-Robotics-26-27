# Underwater Robotics (2026–2027)

**Oregon State University | DAM Robotics — Underwater Robotics Team**

Autonomous and teleoperated Remotely Operated Vehicle (ROV) control system, featuring a Godot 4 Groundstation UI, ROS 2 Humble control pipeline, vectorized 8-thruster allocation, microcontroller firmware (ESP32), computer vision (YOLO crab detection), and an integrated 3D underwater simulation environment.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Repository Structure](#repository-structure)
3. [Subsystems Explained](#subsystems-explained)
   - [Groundstation UI (Godot 4)](#1-groundstation-ui-godot-4)
   - [ROS 2 Control Pipeline (`rov_ctrl_sys`)](#2-ros-2-control-pipeline-rov_ctrl_sys)
   - [Underwater 3D Simulator (`underwater_sim`)](#3-underwater-3d-simulator-underwater_sim)
   - [Microcontroller Firmware (`esp-32-code`)](#4-microcontroller-firmware-esp-32-code)
   - [Computer Vision (`crab_detect`)](#5-computer-vision-crab_detect)
   - [Profiling Float (`float_code`)](#6-profiling-float-float_code)
4. [Controls & Keybindings](#controls--keybindings)
5. [Quickstart Guides](#quickstart-guides)
   - [Local Simulation & Testing (macOS)](#a-local-simulation--testing-on-macos)
   - [Live Mission Deployment (Physical ROV)](#b-live-mission-deployment-physical-rov)
6. [Configuration & Tuning](#configuration--tuning)

---

## System Architecture

```
                       [ OPERATOR STATION ]
   +-----------------------------------------------------------+
   |  Logitech F310 Gamepad / Keyboard                         |
   |                         |                                 |
   |                         v                                 |
   |  Godot 4 Groundstation UI (macOS / Linux)                 |
   |  - Telemetry Dashboard (Thrusters, Depth, Voltage, Servos)|
   |  - Multi-window Camera Feeds (/image_raw)                 |
   |  - ros2_for_godot GDExtension C++ Bridge                  |
   +-----------------------------------------------------------+
                               | ROS 2 DDS Network (Domain 42)
                               v
                       [ ROS 2 PIPELINE ]
   +-----------------------------------------------------------+
   |  /joy ----> joy_to_motor ----> /cmd_vel (TwistStamped)    |
   |                                    |                      |
   |                                    v                      |
   |                            thruster_allocator             |
   |                                    |                      |
   |                                    v                      |
   |                             /motor_command (CSV String)   |
   |                                    |                      |
   |  /key_states -> keyboard_to_servo -> /servo_command       |
   +-----------------------------------------------------------+
                               |
               +---------------+---------------+
               | (Simulation)                  | (Physical Hardware)
               v                               v
    [ underwater_sim ]            [ motor_controller Node ]
    - 3D Seabed & Pipeline        - Serial USB (/dev/esp1, esp2)
    - 6-DOF Hydrodynamics                      |
    - Generates /image_raw                     v
    - Telemetry loop              [ ESP32 Microcontrollers ]
                                  - ESP1: 8x Thruster PWM ESCs
                                  - ESP2: Servos, Lights, Sensors
```

---

## Repository Structure

```
Underwater-Robotics-26-27/
├── run_sim.sh                         # 1-click script: Launches 3D Sim + Godot UI locally
├── run_groundstation.sh               # 1-click script: Launches Godot UI standalone
├── mac_setup.zsh                      # macOS Conda (rov-humble) environment setup
├── ros_setup.sh                       # Linux ROS 2 Humble environment setup
├── ROV.sh                             # Mission launch script (SSH to ROV + local ground)
│
├── underwater-robotics-groundstation/ # Godot 4 Groundstation UI Project
│   ├── project.godot                  # Engine configuration & input mappings
│   ├── main_window.tscn               # Primary control dashboard
│   ├── cameras_window.tscn            # Secondary multi-camera view
│   ├── window_manager.tscn            # Multi-window orchestrator
│   ├── sim/                           # Built-in 3D Simulation Environment (SubViewport)
│   │   ├── sim_world.tscn             # 3D ocean environment (pipeline, seabed, gate, marine life)
│   │   ├── sim_rov.gd                 # 6-DOF ROV hydrodynamic physics, gimbal, and spotlights
│   │   ├── sim_crab.gd                # Benthic crab crawl & animation script
│   │   └── sim_fish.gd                # Marine fish schooling & swimming script
│   ├── scripts/                       # GDScript logic
│   │   ├── ros_interface.gd           # ROS 2 node & topic bridge
│   │   ├── camera_feed.gd             # Multi-threaded image stream decoder & Sim viewport switch
│   │   ├── mode_toggle.gd             # 3D Sim vs Live ROS 2 mode toggle button
│   │   ├── data_output.gd             # Telemetry parsing & label updates
│   │   ├── vertical_movement.gd       # Vertical thruster progress indicators
│   │   ├── lights_control.gd          # Spotlight & dome light sliders
│   │   └── signal_bus.gd              # Event bus decoupler
│   ├── addons/ros2_for_godot/         # GDExtension plugin configuration & binaries
│   └── ros2-for-godot/                # C++ source code for Godot <-> ROS 2 bridge
│
├── ros2_ws/src/rov_ctrl_sys/          # Core ROS 2 Python Package
│   ├── rov_ctrl_sys/
│   │   ├── underwater_sim.py          # 3D Underwater simulator & physics engine
│   │   ├── joy_to_motor.py            # Gamepad sticks -> /cmd_vel (TwistStamped)
│   │   ├── thruster_allocator.py      # 6-DOF mixing matrix -> 8 thruster PWMs
│   │   ├── keyboard_to_servo.py       # Camera pan/tilt & lights intensity tracker
│   │   ├── motor_controller.py        # Serial bridge to ESP32 microcontrollers
│   │   └── window.py                  # Legacy Pygame fallback display
│   ├── launch/
│   │   ├── sim.launch.py              # Simulator + allocator + servo launch
│   │   ├── gamepad.launch.py          # Ground gamepad + allocator launch
│   │   ├── launch_rov.launch.py       # Onboard ROV hardware launch
│   │   └── launch_ground.launch.py    # Local ground station launch
│   └── config/
│       ├── motors.yaml                # Thruster mixing matrix, limits & inversion
│       └── camera.yaml                # Camera resolution & FPS parameters
│
├── esp-32-code/                       # Microcontroller Firmware (C++ / Arduino)
│   ├── esp1/                          # Thruster motor PWM generator (8 ESCs)
│   ├── esp2/                          # Servos, camera gimbal, lights, pressure sensor
│   ├── espA/                          # Ground wireless communication link
│   └── espB/                          # Buoyancy float wireless receiver
│
├── crab_detect/                       # Computer Vision Pipeline
│   ├── yolo.py                        # Live YOLO inference node
│   ├── yolo26n-obb.pt                 # Trained oriented bounding box model
│   └── synthetic_crab_data_generator.py # Synthetic dataset generation tool
│
└── float_code/                        # Profiling Buoyancy Float
    ├── float_comm.py                  # Serial/radio telemetry reader & CSV logger
    └── float_grapher.R                # R analysis & depth plotting script
```

---

## Subsystems Explained

### 1. Groundstation UI (Godot 4)
Located in `underwater-robotics-groundstation/`.

- **Engine**: Godot 4 (Standard 4.7+ without .NET).
- **Architecture**:
  - `window_manager.gd`: Manages multi-monitor layouts, allowing the camera stream to be popped out into an independent window while the telemetry dashboard remains on the main screen.
  - `ros_interface.gd`: Instantiates a `RosNode` (provided by the GDExtension). Subscribes to `/image_raw`, `/motor_command`, and `/servo_command`, and publishes keyboard & gamepad states to `/key_states`.
  - `camera_feed.gd`: Offloads image decoding from the main UI thread to a worker thread via mutex/semaphore synchronization, preventing frame drops during high-throughput 30 FPS video streaming.
  - `vertical_movement.gd`: Averages vertical thruster values (`vfl`, `vfr`, `vbl`, `vbr`) around neutral (1500 µs) and displays live ascending/descending rates on top/bottom progress bars.

#### GDExtension: `ros2_for_godot`
Allows GDScript to directly instantiate ROS 2 nodes, publishers, and subscriptions without intermediary websockets or ROS bridges.
- Located in `underwater-robotics-groundstation/ros2-for-godot/`.
- Written in C++17 against `rclcpp` and `godot-cpp`.
- Custom code generator (`scripts/generate_msgs.py`) automatically generates Godot wrappers for 99 standard ROS 2 message types (`sensor_msgs`, `geometry_msgs`, `std_msgs`, etc.).
- Compiles to `.dylib` on macOS and `.so` on Linux.

---

### 2. ROS 2 Control Pipeline (`rov_ctrl_sys`)
Located in `ros2_ws/src/rov_ctrl_sys/rov_ctrl_sys/`.

#### `joy_to_motor.py`
Reads raw `/joy` inputs from the gamepad and converts them into standardized 6-DOF velocity commands:
- Applies configurable axis deadbands (`0.10`).
- Translates stick inputs into a `geometry_msgs/msg/TwistStamped` message published on `/cmd_vel`:
  - `linear.x`: Surge (forward / backward)
  - `linear.y`: Sway (strafe left / right)
  - `linear.z`: Heave (vertical ascent / descent)
  - `angular.z`: Yaw (heading rotation)
  - `angular.y`: Pitch
  - `angular.x`: Roll

#### `thruster_allocator.py`
Transforms 6-DOF `/cmd_vel` inputs into individual thrust commands for the ROV's **8 vectorized thrusters**:
- **Geometry**:
  - 4 Lateral thrusters at 45° angles (`lfl`, `lfr`, `lbl`, `lbr`).
  - 4 Vertical thrusters for depth, pitch, and roll control (`vfl`, `vfr`, `vbl`, `vbr`).
- **Mixing Formula**:
  $$\text{lfl} = \text{surge} - \text{sway} - \text{yaw}$$
  $$\text{lfr} = \text{surge} + \text{sway} + \text{yaw}$$
  $$\text{lbl} = \text{surge} + \text{sway} - \text{yaw}$$
  $$\text{lbr} = \text{surge} - \text{sway} + \text{yaw}$$
  $$\text{vfl} = \text{heave} + \text{pitch} - \text{roll}$$
  $$\text{vfr} = \text{heave} + \text{pitch} + \text{roll}$$
  $$\text{vbl} = \text{heave} - \text{pitch} - \text{roll}$$
  $$\text{vbr} = \text{heave} - \text{pitch} + \text{roll}$$
- **PWM Output**: Converts normalized `[-1.0, 1.0]` thrust to standard ESC microsecond pulses (`1100 µs` full reverse, `1500 µs` neutral, `1900 µs` full forward).
- **Idle Timers**: Automatically fires a one-shot safety neutral packet (`1500`) when control sticks are released to prevent thrusters from running continuously if a packet is dropped.

#### `keyboard_to_servo.py`
Listens to `/key_states` from the UI and manages incremental control for auxiliary servos and lighting:
- Keeps track of target selection: Camera Gimbal (`C`), Dome Lights (`D`), or Exterior Lights (`E`).
- Increments / decrements tilt (`camera_y`), pan (`camera_x`), or brightness (`ext_lights_max`, `dome_lights_max`).
- Publishes updates to `/servo_command`.

#### `motor_controller.py`
The hardware serial bridge:
- Connects to the primary microcontroller via `/dev/esp1` at 115200 baud.
- Packages thruster PWMs into lightweight serial strings (`lfl=1600,lfr=1400...`) for the ESP32.

---

### 3. Underwater 3D Simulator (`underwater_sim`)
Located in `ros2_ws/src/rov_ctrl_sys/rov_ctrl_sys/underwater_sim.py`.

A native, lightweight 3D simulation environment built for testing on macOS without needing Gazebo:
- **Renderer**: Uses headless Pygame with double buffering, outputting `sensor_msgs/msg/Image` frames (`rgb8`, 640x480) directly into `/image_raw` at 30 FPS.
- **Scene Features**:
  - Textured seabed with depth perspective grid and 3D rocks.
  - Subsea pipeline with industrial hazard markings.
  - Underwater inspection hoop/gate beacon.
  - Animated marine life (crabs crawling on the seafloor, swimming fish).
  - Drifting marine snow particulates.
  - Dynamic headlights: Conical spotlight projections that respond to `/servo_command` (`dome_lights_max` and `ext_lights_max`).
- **Gimbal Simulation**: Camera pan and tilt rotate the 3D perspective in real time according to `/servo_command`.
- **Physics**: 6-DOF motion model with quadratic hydrodynamic drag ($F_{drag} \propto -v|v|$) and depth clamping.

---

### 4. Microcontroller Firmware (`esp-32-code`)
Located in `esp-32-code/`.

- **ESP 1 (`esp1/esp1.ino`)**:
  - Handles the 8 brushless thruster ESCs using ESP32 hardware LEDC PWM timers (50 Hz, 16-bit resolution).
  - Includes a motor slowdown safety rate-limiter to prevent sudden direction reversals that can trigger high-current voltage spikes.
- **ESP 2 (`esp2/esp2.ino`)**:
  - Drives auxiliary servos: Camera pan/tilt servos and the manipulator claw (open/close and continuous rotation).
  - Drives MOSFET PWM circuits for high-lumen external LED headlights.
  - Reads analog and I2C sensors (depth pressure transducer, internal temperature).

---

### 5. Computer Vision (`crab_detect`)
Located in `crab_detect/`.

- Real-time detection of benthic targets (crabs) for MATE ROV competition tasks.
- Trained using YOLOv8/v11 Oriented Bounding Boxes (`yolo26n-obb.pt`) to detect position and rotation angle of target objects on the seabed.
- Includes `synthetic_crab_data_generator.py` for augmenting real-world training images with simulated water turbidity, light falloff, and color distortions.

---

### 6. Profiling Float (`float_code`)
Located in `float_code/`.

- Controls an autonomous buoyancy-driven profiling float.
- `float_comm.py`: Communicates with ESP-A/B transceiver pairs to log pressure, salinity, and depth measurements to CSV.
- `float_grapher.R`: Generates profile depth-time plots and descent velocity curves.

---

## Controls & Keybindings

### Flight & Driving Controls
| Action | Keyboard | Logitech Gamepad F310 |
| :--- | :--- | :--- |
| **Surge (Forward / Reverse)** | `W` / `S` | Left Stick Vertical |
| **Sway (Strafe Left / Right)** | `A` / `D` | Left Stick Horizontal |
| **Yaw (Turn Left / Right)** | `Q` / `E` | Right Stick Horizontal |
| **Heave (Ascend / Surface)** | `Space` | Right Trigger (`RT`) |
| **Heave (Descend / Dive)** | `Shift` | Left Trigger (`LT`) |

### Camera & Auxiliary Controls
| Action | Key Sequence | Description |
| :--- | :--- | :--- |
| **Select Camera Gimbal** | `C` | Targets camera for pan/tilt adjustments |
| **Camera Tilt** | `C` then `↑` / `↓` | Tilts camera mount up or down |
| **Camera Pan** | `C` then `←` / `→` | Pans camera mount left or right |
| **Camera Center** | `Backspace` | Resets camera gimbal to center |
| **Select Exterior Lights** | `E` | Targets external spotlights |
| **Adjust Light Intensity** | `E` then `↑` / `↓` | Brightens or dims external spotlights |
| **Select Dome Lights** | `D` | Targets internal dome illumination |
| **Adjust Dome Intensity** | `D` then `↑` / `↓` | Brightens or dims dome illumination |

### UI Window Controls
| Action | Key | Description |
| :--- | :--- | :--- |
| **Toggle Fullscreen** | `F` | Toggles fullscreen mode for the groundstation |
| **Close Application** | `Shift` + `Esc` | Safely disconnects and shuts down the UI |
| **Test Diagnostic Error** | `P` | Emits a test error to the groundstation error console |

---

## Installation & Setup Guides

### macOS Setup Guide (Apple Silicon & Intel)

#### 1. Prerequisites
- **Xcode Command Line Tools**:
  ```bash
  xcode-select --install
  ```
- **Conda / Miniforge** (recommended for ROS 2 on macOS):
  Install [Miniforge](https://github.com/conda-forge/miniforge) or [Anaconda](https://www.anaconda.com/download).

#### 2. Create the `rov-humble` Conda Environment
From the repository root, install the required packages (Robostack ROS 2 Humble, Python 3.11, Colcon, Pygame, PySerial):
```bash
cd ~/Underwater-Robotics-26-27
conda env create -f environment.yaml
conda activate rov-humble
```

#### 3. Download Godot 4
- Download **Godot 4.7+ Standard (non-.NET)** for macOS from the [Godot Engine Download Archive](https://godotengine.org/download/archive/):
  - Download: `Godot_v4.7.2-stable_macos.universal.zip`
  - Unzip and move `Godot.app` into `~/Downloads/` or `/Applications/`.

#### 4. Build the ROS 2 Workspace
```bash
conda activate rov-humble
source mac_setup.zsh
cd ros2_ws
colcon build --symlink-install
```

#### 5. Build or Verify `ros2_for_godot` GDExtension (macOS)
The precompiled macOS arm64 library is included in `underwater-robotics-groundstation/addons/ros2_for_godot/bin/macos/libros2_for_godot.dylib`.
If you need to recompile it from source:
```bash
conda activate rov-humble
cd underwater-robotics-groundstation/ros2-for-godot
cmake -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=$AMENT_PREFIX_PATH
cmake --build build -j$(sysctl -n hw.ncpu)
cp build/bin/libros2_for_godot.dylib ../addons/ros2_for_godot/bin/macos/
```

#### 6. Logitech F310 Gamepad Configuration on macOS
1. **Switch to DirectInput Mode**: Check the physical slide switch on the back of the controller labeled `[ X | D ]`. Flip it to **`D`**. *(The `X` position uses Windows XInput which macOS cannot read as a standard joystick without third-party kexts).*
2. **Quit Steam**: Steam running on macOS claims exclusive USB access to controllers (`steam_osx`). Completely quit Steam (`⌘ + Q`) before launching the Groundstation.

#### 7. Run the Simulation Locally
You have two local simulation modes available:

- **Option 1: Built-in 3D Godot Simulator (Recommended)**
  Directly renders a 3D ocean scene (seabed, subsea pipeline, inspection gate, benthic crabs, schooling fish, and full 6-DOF ROV physics with headlights) inside the Groundstation UI:
  ```bash
  ~/Underwater-Robotics-26-27/run_groundstation.sh
  ```
  *(Click the `3D Simulator Mode [ON]` button in the top right at any time to toggle between the 3D sim world and live ROS 2 camera feed).*

- **Option 2: Standalone ROS 2 Python Simulator**
  Launches the Python-based ROS 2 underwater simulator node (`underwater_sim.py`) with naval HUD and camera streaming over ROS 2 `/image_raw`:
  ```bash
  ~/Underwater-Robotics-26-27/run_sim.sh
  ```

---

### Ubuntu Linux Setup Guide (Ubuntu 22.04 LTS)

#### 1. System Dependencies & ROS 2 Humble
Install ROS 2 Humble following the standard OSRF repository instructions:
```bash
sudo apt update && sudo apt install -y software-properties-common curl gnupg lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update && sudo apt install -y \
    ros-humble-ros-base \
    ros-humble-joy \
    python3-colcon-common-extensions \
    python3-pip \
    git \
    cmake \
    g++ \
    zip
```

#### 2. Python Packages
```bash
pip3 install pygame pyserial pytest
```

#### 3. USB Permissions & Udev Rules
Add your user to the `dialout` group to communicate with the ESP32 serial interfaces:
```bash
sudo usermod -a -G dialout $USER
```

Create udev rules for predictable microcontroller symlinks (`/dev/esp1`, `/dev/esp2`):
```bash
# Identify your devices
udevadm info --attribute-walk --name=/dev/ttyUSB0 | grep -E "idVendor|idProduct|serial"

# Add rules to /etc/udev/rules.d/99-rov.rules
sudo tee /etc/udev/rules.d/99-rov.rules << 'EOF'
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="esp1", MODE="0666"
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="esp2", MODE="0666"
EOF

sudo udevadm control --reload-rules && sudo udevadm trigger
```

#### 4. Download Godot 4 for Linux
- Download **Godot 4.7+ Standard (x86_64 or arm64)** from the [Godot Engine Download Archive](https://godotengine.org/download/archive/):
  ```bash
  wget https://github.com/godotengine/godot/releases/download/4.7.1-stable/Godot_v4.7.1-stable_linux.x86_64.zip
  unzip Godot_v4.7.1-stable_linux.x86_64.zip
  chmod +x Godot_v4.7.1-stable_linux.x86_64
  sudo mv Godot_v4.7.1-stable_linux.x86_64 /usr/local/bin/godot
  ```

#### 5. Build GDExtension for Linux
```bash
source /opt/ros/humble/setup.bash
cd ~/Underwater-Robotics-26-27/underwater-robotics-groundstation/ros2-for-godot
./build.sh --overlay Release
./create_addon.sh
# Copy generated binary to addons folder:
mkdir -p ../addons/ros2_for_godot/bin/linux.x86_64/
cp build/bin/libros2_for_godot.so ../addons/ros2_for_godot/bin/linux.x86_64/
```

#### 6. Build the ROS 2 Workspace
```bash
cd ~/Underwater-Robotics-26-27
source ros_setup.sh
cd ros2_ws
colcon build --symlink-install
```

#### 7. Launching Groundstation on Ubuntu
```bash
source ~/Underwater-Robotics-26-27/ros_setup.sh
godot --path ~/Underwater-Robotics-26-27/underwater-robotics-groundstation
```

---

## Quickstart Guides

### A. Local Simulation & Testing (on macOS)

You can test and fly the ROV locally without any physical hardware using either simulation method:

#### 1. Integrated 3D Godot Simulation (Built-in)
Runs directly inside Godot with hardware-accelerated 3D graphics, dynamic underwater fog, benthic fauna, and interactive headlights:
```bash
~/Underwater-Robotics-26-27/run_groundstation.sh
```
- **Controls**:
  - `W` / `S`: Surge Forward / Backward
  - `A` / `D`: Sway Left / Right
  - `Q` / `E`: Yaw Turn Left / Right
  - `Space` / `Shift`: Heave Ascend / Dive
  - `I` / `K`: Camera Tilt Up / Down
  - `J` / `L`: Camera Pan Left / Right
  - `F`: Toggle Dual Spotlight Headlights
  - Gamepad: Left stick (Surge/Sway), Right stick X (Yaw), Triggers (Ascend/Descend)
- **Mode Toggle**: Click `3D Simulator Mode [ON]` in the top right to switch between the 3D scene and live ROS 2 camera stream on the fly.

#### 2. Standalone ROS 2 Python Simulator (`underwater_sim.py`)
Runs the ROS 2 physics node publishing camera frames over `/image_raw` and telemetry:
```bash
~/Underwater-Robotics-26-27/run_sim.sh
```
This launcher automatically sources Conda (`rov-humble`), launches `sim.launch.py`, and brings up the Groundstation.

> **Logitech F310 Gamepad on Mac:**
> - Ensure **Steam is closed** (`⌘ + Q`), as Steam claims exclusive USB ownership (`steam_osx`) and blocks other programs from reading gamepad events.
> - Ensure the switch on the back of the controller is flipped to **`D` (DirectInput)**, not `X` (XInput).

---

### B. Live Mission Deployment (Physical ROV)

When connected to the ROV over the tether network:

#### 1. Onboard the ROV (via SSH)
```bash
ssh -t ROV
source ~/Underwater-Robotics-Current/ros_setup.sh
ros2 launch rov_ctrl_sys launch_rov.launch.py
```

#### 2. On Your Groundstation Computer
```bash
# Terminal 1: Ground nodes & gamepad
cd ~/Underwater-Robotics-26-27
source mac_setup.zsh   # Or source ros_setup.sh on Linux
ros2 launch rov_ctrl_sys gamepad.launch.py

# Terminal 2: Groundstation UI
~/Underwater-Robotics-26-27/run_groundstation.sh
```

---

## Configuration & Tuning

- **Thruster Gains & Limits**: Edit `ros2_ws/src/rov_ctrl_sys/config/motors.yaml` to adjust `lateral_cap`, `vertical_cap`, joystick deadzones, or thruster reverse multipliers.
- **Camera Settings**: Edit `ros2_ws/src/rov_ctrl_sys/config/camera.yaml` to configure camera resolution, frame rates, and encoding.
- **Godot Project Settings**: Edit `underwater-robotics-groundstation/project.godot` to rebind keys or adjust display window modes.
