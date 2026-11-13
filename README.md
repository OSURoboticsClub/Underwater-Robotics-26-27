# Underwater Robotics (2026–2027)

**Oregon State University | DAM Robotics — Underwater Robotics Team**

Control system and operator groundstation for the OSU Remotely Operated Vehicle (ROV). Includes an integrated Godot 4 Groundstation UI, ROS 2 Humble control pipeline, 8-thruster vector allocation, microcontroller firmware (ESP32), computer vision (YOLO target detection), and local 3D simulation.

---

## System Architecture

```
                       [ OPERATOR STATION ]
   +-----------------------------------------------------------+
   |  Logitech F310 Gamepad / Keyboard                         |
   |                         |                                 |
   |                         v                                 |
   |  Godot 4 Groundstation UI (macOS / Linux)                 |
   |  - Real-time Telemetry (Thrusters, Depth, Voltage, Lights)|
   |  - Video Stream Display (/image_raw)                      |
   |  - Integrated 3D Underwater Simulation Viewport           |
   |  - Native ros2_for_godot GDExtension C++ Bridge           |
   +-----------------------------------------------------------+
                                | ROS 2 DDS (Domain 42)
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

## Repository Layout

```
Underwater-Robotics-26-27/
├── setup_ubuntu.sh                    # 1-click full environment setup for Ubuntu
├── run_groundstation.sh               # Launch Godot UI (+ optional 3D Sim)
├── run_sim.sh                         # Launch full ROS 2 Python simulator + Godot UI
├── mac_setup.zsh                      # macOS Conda environment loader
├── ros_setup.sh                       # Linux ROS 2 environment loader
├── ROV.sh                             # Mission launch script (SSH to ROV + ground)
│
├── underwater-robotics-groundstation/ # Godot 4 Operator Dashboard
│   ├── main_window.tscn               # Main dashboard UI
│   ├── sim/                           # Built-in 3D Ocean Simulation (SubViewport)
│   │   ├── sim_world.tscn             # 3D seafloor, pipeline, gates, marine life
│   │   ├── sim_rov.gd                 # 6-DOF ROV hydrodynamics, gimbal & lights
│   │   ├── sim_crab.gd                # Benthic crab crawl animation
│   │   └── sim_fish.gd                # Schooling fish behavior
│   ├── scripts/                       # Groundstation GDScript logic
│   │   ├── ros_interface.gd           # ROS 2 node & topic bridge
│   │   ├── camera_feed.gd             # Multi-threaded video receiver & texture updater
│   │   ├── mode_toggle.gd             # 3D Sim vs Live Camera toggle button
│   │   ├── data_output.gd             # Telemetry label updater
│   │   ├── lights_control.gd          # Headlights & dome light controls
│   │   └── signal_bus.gd              # Event bus
│   ├── addons/ros2_for_godot/         # GDExtension configuration & platform binaries
│   └── ros2-for-godot/                # C++ bridge source (rclcpp <-> godot-cpp)
│
├── ros2_ws/src/rov_ctrl_sys/          # Core ROS 2 Python Package
│   ├── rov_ctrl_sys/
│   │   ├── joy_to_motor.py            # Gamepad stick parsing -> 6-DOF /cmd_vel
│   │   ├── thruster_allocator.py      # 6-DOF mixing matrix -> 8 thruster PWMs
│   │   ├── keyboard_to_servo.py       # Camera pan/tilt & light intensity state
│   │   ├── motor_controller.py        # Serial communication to ESP32s
│   │   └── underwater_sim.py          # Standalone 3D line-rendering simulator & HUD
│   ├── launch/                        # Launch files (sim, gamepad, ROV hardware)
│   └── config/motors.yaml             # Thruster mixing matrix, caps & inversion
│
├── esp-32-code/                       # Microcontroller Firmware (C++ / Arduino)
│   ├── esp1/                          # 8x Thruster PWM ESC signal generation
│   └── esp2/                          # Servos, camera gimbal, lights, pressure sensor
│
├── crab_detect/                       # Computer Vision Pipeline (YOLOv8/v11 OBB)
└── float_code/                        # Autonomous Profiling Float reader & analysis
```

---

## Thruster Allocation & Mixing

The ROV employs an 8-thruster vectorized configuration:
- 4 Lateral thrusters mounted at 45° horizontal angles (`lfl`, `lfr`, `lbl`, `lbr`).
- 4 Vertical thrusters for depth, pitch, and roll control (`vfl`, `vfr`, `vbl`, `vbr`).

### Mixing Matrix
$$\begin{aligned}
\text{lfl} &= \text{surge} - \text{sway} - \text{yaw} \\
\text{lfr} &= \text{surge} + \text{sway} + \text{yaw} \\
\text{lbl} &= \text{surge} + \text{sway} - \text{yaw} \\
\text{lbr} &= \text{surge} - \text{sway} + \text{yaw} \\
\text{vfl} &= \text{heave} + \text{pitch} - \text{roll} \\
\text{vfr} &= \text{heave} + \text{pitch} + \text{roll} \\
\text{vbl} &= \text{heave} - \text{pitch} - \text{roll} \\
\text{vbr} &= \text{heave} - \text{pitch} + \text{roll}
\end{aligned}$$

Outputs are clamped to standard ESC PWM ranges (1100 µs full reverse, 1500 µs neutral, 1900 µs full forward). Releasing sticks automatically emits a 1500 µs neutral safety packet.

---

## Controls

### Flight Controls
| Motion | Keyboard | Logitech Gamepad F310 |
| :--- | :--- | :--- |
| **Surge (Forward / Reverse)** | `W` / `S` | Left Stick Vertical |
| **Sway (Strafe Left / Right)** | `A` / `D` | Left Stick Horizontal |
| **Yaw (Turn Left / Right)** | `Q` / `E` | Right Stick Horizontal |
| **Heave (Surface / Ascend)** | `Space` | Right Trigger (`RT`) |
| **Heave (Dive / Descend)** | `Shift` | Left Trigger (`LT`) |

### Camera Gimbal & Lighting
| Function | Key Sequence |
| :--- | :--- |
| **Camera Tilt** | `I` / `K` (or `C` then `↑` / `↓`) |
| **Camera Pan** | `J` / `L` (or `C` then `←` / `→`) |
| **Camera Reset** | `Backspace` |
| **Toggle Dual Spotlights** | `F` (or `E` then `↑` / `↓` for intensity) |
| **Dome Light Intensity** | `D` then `↑` / `↓` |

### Mode Switching
- Click the **`3D Simulator Mode [ON]` / `Live ROS 2 Mode [ON]`** button in the top-right corner to toggle between the simulated 3D ocean environment and the live camera stream on the fly.

---

## Setup & Running

### Option A: Ubuntu Linux (22.04 / 24.04 LTS)

#### 1-Click Automated Setup
```bash
git clone https://github.com/OSURoboticsClub/Underwater-Robotics-26-27.git
cd Underwater-Robotics-26-27
./setup_ubuntu.sh
```

#### Launching
```bash
./run_groundstation.sh   # Integrated 3D Godot Sim & UI
# OR
./run_sim.sh             # Full ROS 2 Python Simulator + Godot UI
```

---

### Option B: macOS (Apple Silicon & Intel)

#### 1. Setup Conda Environment
Install Miniforge or Anaconda, then:
```bash
cd ~/Underwater-Robotics-26-27
conda env create -f environment.yaml
conda activate rov-humble
source mac_setup.zsh
```

#### 2. Install Godot 4
Download Godot 4 (Standard, non-.NET) from [godotengine.org](https://godotengine.org/download) into `/Applications` or `~/Downloads`.

#### 3. Gamepad Notes (macOS)
- **Controller Switch**: Flip the switch on the back of the Logitech F310 to **`D` (DirectInput)**.
- **Steam**: Quit Steam completely (`⌘ + Q`); Steam takes exclusive USB control of controllers and blocks ROS/Godot from reading axes.

#### 4. Launching
```bash
./run_groundstation.sh   # Integrated 3D Godot Sim & UI
# OR
./run_sim.sh             # Full ROS 2 Python Simulator + Godot UI
```

---

### Physical ROV Mission Deployment

When connected to the physical ROV tether network:

1. **Onboard the ROV (via SSH)**:
   ```bash
   ssh -t ROV
   source ~/Underwater-Robotics-26-27/ros_setup.sh
   ros2 launch rov_ctrl_sys launch_rov.launch.py
   ```

2. **Groundstation Computer**:
   ```bash
   # Terminal 1: Gamepad & control nodes
   source mac_setup.zsh   # or source ros_setup.sh on Linux
   ros2 launch rov_ctrl_sys gamepad.launch.py

   # Terminal 2: Groundstation UI
   ./run_groundstation.sh
   ```

---

## Microcontroller Configuration

ESP32s communicate over USB serial at 115200 baud:
- **`/dev/esp1`**: Drives 8 brushless motor ESCs via hardware LEDC PWM timers (50 Hz). Includes deceleration rate-limiting to prevent reverse current spikes.
- **`/dev/esp2`**: Drives camera pan/tilt servos, manipulator claw, spotlight MOSFETs, and reads depth pressure transducers.

Add udev rules on Linux (`/etc/udev/rules.d/99-rov.rules`) for persistent symlinks:
```udev
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="esp1", MODE="0666"
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="esp2", MODE="0666"
```
Reload rules:
```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```
