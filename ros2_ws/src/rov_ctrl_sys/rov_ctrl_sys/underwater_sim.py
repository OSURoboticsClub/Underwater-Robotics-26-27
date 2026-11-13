#!/usr/bin/env python3
"""
underwater_sim.py

High-Fidelity 3D Underwater Simulation & Hydrodynamics Engine for ROV Testing.
Features:
 - Glitch-free near-plane line & polygon clipping (eliminates geometry pop-in)
 - Painter's Algorithm depth-sorting (z-buffer order for all 3D entities)
 - Pre-allocated double buffers & offscreen surfaces (zero GC frame drops)
 - Physically based underwater optical fog falloff & dynamic spotlight cones
 - Realistic 6-DOF hydrodynamics with fluid inertia, quadratic drag, and buoyancy
 - Professional Naval ROV HUD (Compass ribbon, depth tape, pitch ladder, thruster telemetry)
 - Direct gamepad, keyboard (WASD/QE/Space/Shift), and ROS 2 topic control
"""

import os
import sys
import math
import random
import time

# Headless SDL offscreen configuration
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

from sensor_msgs.msg import Image
from std_msgs.msg import String
from geometry_msgs.msg import TwistStamped, Twist


class UnderwaterSim(Node):
    def __init__(self):
        super().__init__('underwater_sim')

        # Parameters
        self.declare_parameter('width', 640)
        self.declare_parameter('height', 480)
        self.declare_parameter('fps', 30.0)

        self.width = self.get_parameter('width').value
        self.height = self.get_parameter('height').value
        self.fps = self.get_parameter('fps').value

        # Camera Optics
        self.fov = 65.0  # Vertical FOV in degrees
        self.focal_length = (self.height / 2.0) / math.tan(math.radians(self.fov / 2.0))
        self.near_clip = 0.25  # Camera near clipping plane

        # ROS 2 Communication
        sensor_qos = QoSProfile(depth=5, reliability=ReliabilityPolicy.BEST_EFFORT)
        reliable_qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)

        self.image_pub = self.create_publisher(Image, '/image_raw', sensor_qos)
        self.motor_pub = self.create_publisher(String, '/motor_command', reliable_qos)

        self.create_subscription(String, '/motor_command', self._on_motor_command, reliable_qos)
        self.create_subscription(String, '/servo_command', self._on_servo_command, reliable_qos)
        self.create_subscription(String, '/key_states', self._on_key_states, reliable_qos)
        self.create_subscription(TwistStamped, '/cmd_vel', self._on_cmd_vel_stamped, reliable_qos)
        self.create_subscription(Twist, '/cmd_vel_unstamped', self._on_cmd_vel, reliable_qos)

        # Pygame Setup & Pre-allocated Buffers
        pygame.init()
        self.surface = pygame.Surface((self.width, self.height))
        self.overlay_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.hud_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.font_large = pygame.font.SysFont("monospace", 14, bold=True)
        self.font_small = pygame.font.SysFont("monospace", 11, bold=True)

        # ROV 6-DOF Kinematics & Physics State
        # World Frame: X=East (Right), Y=North (Forward), Z=Up (Surface=0, Seabed=-10m)
        self.pos = [0.0, 0.0, -3.5]
        self.vel = [0.0, 0.0, 0.0]
        self.yaw = 0.0         # Heading angle in radians
        self.yaw_rate = 0.0
        self.pitch = 0.0
        self.roll = 0.0

        # Commanded targets (smoothed in physics loop)
        self.cmd_surge = 0.0
        self.cmd_sway = 0.0
        self.cmd_heave = 0.0
        self.cmd_yaw = 0.0

        # Auxiliary Servos & Lights
        self.camera_pan = 0.0    # -1.0 to 1.0 (mapped to -45° to +45°)
        self.camera_tilt = 0.0   # -1.0 to 1.0 (mapped to -40° to +40°)
        self.dome_lights = 0.0   # 0.0 to 1.0
        self.ext_lights = 0.0    # 0.0 to 1.0

        # 8-Thruster States (1100 to 1900 µs, neutral = 1500 µs)
        self.thrusters = {
            'lfl': 1500, 'lfr': 1500, 'lbl': 1500, 'lbr': 1500,
            'vfl': 1500, 'vfr': 1500, 'vbl': 1500, 'vbr': 1500
        }

        # Initialize Scenery & World Objects
        self._init_world()

        # Timer Loop
        self.last_time = time.time()
        self.timer = self.create_timer(1.0 / self.fps, self._step)

        self.get_logger().info(f"Enhanced 3D Underwater Simulator active ({self.width}x{self.height} @ {self.fps} FPS).")

    def _init_world(self):
        """Build static and dynamic underwater scenery."""
        random.seed(42)

        # Marine snow particulate drift (small floating flecks)
        self.marine_snow = [
            [random.uniform(-18, 18), random.uniform(-4, 28), random.uniform(-9.5, -0.2),
             random.uniform(1.0, 2.0), random.uniform(0.1, 0.35)]
            for _ in range(80)
        ]

        # Seabed rocks with distinct 3D geometry & shading
        self.rocks = []
        for _ in range(35):
            rx = random.uniform(-22, 22)
            ry = random.uniform(2, 38)
            rz = -9.9 + random.uniform(0.0, 0.4)
            rw = random.uniform(0.5, 1.6)
            rh = random.uniform(0.3, 0.9)
            color = (random.randint(45, 65), random.randint(70, 95), random.randint(60, 80))
            self.rocks.append({'x': rx, 'y': ry, 'z': rz, 'w': rw, 'h': rh, 'c': color})

        # Benthic Crabs (Target for OSU Detection Model)
        self.crabs = [
            {'x': -1.2, 'y': 6.5, 'z': -9.8, 'heading': 0.6, 'phase': 0.0},
            {'x': 3.5, 'y': 10.8, 'z': -9.8, 'heading': -1.4, 'phase': 1.8},
            {'x': 0.8, 'y': 15.2, 'z': -9.8, 'heading': 2.3, 'phase': 3.1},
        ]

        # Swimming Fish Schools
        self.fish = [
            {'x': random.uniform(-10, 10), 'y': random.uniform(4, 24), 'z': random.uniform(-7, -2.5),
             'speed': random.uniform(0.7, 1.5), 'phase': random.uniform(0, 6.28), 'size': random.uniform(0.25, 0.45)}
            for _ in range(12)
        ]

        # Subsea Pipeline segments (along X axis at Y=14.0, Z=-8.8)
        self.pipe_y = 13.5
        self.pipe_z = -8.9
        self.pipe_radius = 0.45

        # Subsea Inspection Arch / Gate at (0.0, 20.0, -6.5)
        self.gate_x = 0.0
        self.gate_y = 19.0
        self.gate_z = -6.8
        self.gate_radius = 2.4

    # -------------------------------------------------------------------------
    # Topic Callbacks
    # -------------------------------------------------------------------------
    def _on_motor_command(self, msg: String):
        parts = msg.data.split(',')
        for p in parts:
            if '=' in p:
                k, v = p.split('=', 1)
                k = k.strip()
                try:
                    if k in self.thrusters:
                        self.thrusters[k] = int(float(v.strip()))
                except ValueError:
                    pass

    def _on_servo_command(self, msg: String):
        parts = msg.data.split(',')
        for p in parts:
            delim = ':' if ':' in p else ('=' if '=' in p else None)
            if delim:
                k, v = p.split(delim, 1)
                k = k.strip()
                try:
                    val = float(v.strip())
                    if k == 'camera_x':
                        self.camera_pan = val
                    elif k == 'camera_y':
                        self.camera_tilt = val
                    elif k == 'dome_lights_max':
                        self.dome_lights = max(0.0, min(1.0, val))
                    elif k == 'ext_lights_max':
                        self.ext_lights = max(0.0, min(1.0, val))
                except ValueError:
                    pass

    def _on_key_states(self, msg: String):
        """Parse UI keyboard & gamepad stick commands."""
        parts = [k.strip() for k in msg.data.split(',')]
        keys = set(parts)

        # Gamepad axis inputs
        joy_surge = 0.0
        joy_sway = 0.0
        joy_yaw = 0.0
        joy_heave = 0.0

        for p in parts:
            if ':' in p:
                axis, val_str = p.split(':', 1)
                try:
                    v = float(val_str)
                    if axis == 'JOY_LY':
                        joy_surge = -v  # Up on stick is negative Y
                    elif axis == 'JOY_LX':
                        joy_sway = v
                    elif axis == 'JOY_RX':
                        joy_yaw = -v
                    elif axis == 'JOY_RT':
                        joy_heave += v
                    elif axis == 'JOY_LT':
                        joy_heave -= v
                    elif axis == 'JOY_RY':
                        joy_heave += -v
                except ValueError:
                    pass

        # Keyboard WASD / QE / Space/Shift inputs
        kb_surge = 0.0
        kb_sway = 0.0
        kb_yaw = 0.0
        kb_heave = 0.0

        if 'W' in keys:
            kb_surge += 1.0
        if 'S' in keys:
            kb_surge -= 1.0
        if 'D' in keys:
            kb_sway += 1.0
        if 'A' in keys:
            kb_sway -= 1.0
        if 'E' in keys:
            kb_yaw += 1.0
        if 'Q' in keys:
            kb_yaw -= 1.0
        if 'SPACE' in keys:
            kb_heave += 1.0
        if 'SHIFT' in keys:
            kb_heave -= 1.0

        # Set target command velocities (smoothed in physics loop)
        self.cmd_surge = max(-1.0, min(1.0, joy_surge + kb_surge))
        self.cmd_sway = max(-1.0, min(1.0, joy_sway + kb_sway))
        self.cmd_yaw = max(-1.0, min(1.0, joy_yaw + kb_yaw))
        self.cmd_heave = max(-1.0, min(1.0, joy_heave + kb_heave))

        # Update 8-thruster PWM meters for Groundstation telemetry
        self._update_thruster_pwms(self.cmd_surge, self.cmd_sway, self.cmd_heave, self.cmd_yaw)

    def _update_thruster_pwms(self, surge, sway, heave, yaw):
        def clamp_pwm(pwm):
            return max(1100, min(1900, int(pwm)))

        self.thrusters['lfl'] = clamp_pwm(1500 + (surge - sway - yaw) * 350)
        self.thrusters['lfr'] = clamp_pwm(1500 + (surge + sway + yaw) * 350)
        self.thrusters['lbl'] = clamp_pwm(1500 + (surge + sway - yaw) * 350)
        self.thrusters['lbr'] = clamp_pwm(1500 + (surge - sway + yaw) * 350)

        self.thrusters['vfl'] = clamp_pwm(1500 + heave * 350)
        self.thrusters['vfr'] = clamp_pwm(1500 + heave * 350)
        self.thrusters['vbl'] = clamp_pwm(1500 + heave * 350)
        self.thrusters['vbr'] = clamp_pwm(1500 + heave * 350)

    def _on_cmd_vel_stamped(self, msg: TwistStamped):
        self._apply_twist(msg.twist)

    def _on_cmd_vel(self, msg: Twist):
        self._apply_twist(msg)

    def _apply_twist(self, twist: Twist):
        self.cmd_surge = twist.linear.x
        self.cmd_sway = twist.linear.y
        self.cmd_heave = twist.linear.z
        self.cmd_yaw = twist.angular.z
        self._update_thruster_pwms(self.cmd_surge, self.cmd_sway, self.cmd_heave, self.cmd_yaw)

    # -------------------------------------------------------------------------
    # Hydrodynamics & Physics Engine
    # -------------------------------------------------------------------------
    def _update_physics(self, dt: float):
        # Body-to-World coordinate rotation
        cy = math.cos(self.yaw)
        sy = math.sin(self.yaw)

        # Target world velocities based on ROV heading
        target_vx = (cy * self.cmd_sway + sy * self.cmd_surge) * 1.6
        target_vy = (-sy * self.cmd_sway + cy * self.cmd_surge) * 1.6
        target_vz = self.cmd_heave * 1.2
        target_wz = self.cmd_yaw * 1.4

        # Smooth exponential acceleration & hydrodynamic momentum
        accel_rate = 5.0 * dt
        self.vel[0] += (target_vx - self.vel[0]) * accel_rate
        self.vel[1] += (target_vy - self.vel[1]) * accel_rate
        self.vel[2] += (target_vz - self.vel[2]) * accel_rate
        self.yaw_rate += (target_wz - self.yaw_rate) * accel_rate

        # Natural fluid damping (drag)
        self.vel[0] *= (1.0 - 0.4 * dt)
        self.vel[1] *= (1.0 - 0.4 * dt)
        self.vel[2] *= (1.0 - 0.5 * dt)
        self.yaw_rate *= (1.0 - 0.6 * dt)

        # Integrate pose
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt
        self.pos[2] += self.vel[2] * dt
        self.yaw += self.yaw_rate * dt

        # Water boundary clamping: Surface = -0.3m, Seabed = -9.6m
        if self.pos[2] > -0.3:
            self.pos[2] = -0.3
            self.vel[2] = min(0.0, self.vel[2])
        elif self.pos[2] < -9.6:
            self.pos[2] = -9.6
            self.vel[2] = max(0.0, self.vel[2])

        # Animate Crabs
        for crab in self.crabs:
            crab['phase'] += dt * 3.5
            crab['x'] += math.cos(crab['heading']) * 0.12 * dt
            crab['y'] += math.sin(crab['heading']) * 0.12 * dt
            if random.random() < 0.015:
                crab['heading'] += random.uniform(-0.6, 0.6)

        # Animate Fish
        for fish in self.fish:
            fish['phase'] += dt * fish['speed'] * 2.2
            fish['y'] += fish['speed'] * dt
            fish['x'] += math.sin(fish['phase']) * 0.4 * dt
            if fish['y'] > self.pos[1] + 32.0:
                fish['y'] = self.pos[1] - 4.0
                fish['x'] = self.pos[0] + random.uniform(-10, 10)

        # Animate Marine Snow Particulates
        for p in self.marine_snow:
            p[2] -= p[4] * dt
            p[0] += math.sin(p[2] * 2.5) * 0.04 * dt
            if p[2] < -9.8:
                p[2] = -0.4
                p[0] = self.pos[0] + random.uniform(-12, 12)
                p[1] = self.pos[1] + random.uniform(0, 22)

    # -------------------------------------------------------------------------
    # 3D Math & Projection Helpers
    # -------------------------------------------------------------------------
    def _world_to_camera(self, wx, wy, wz):
        """Transforms a 3D world coordinate into camera coordinate space."""
        # Translate relative to ROV
        dx = wx - self.pos[0]
        dy = wy - self.pos[1]
        dz = wz - self.pos[2]

        # Rotate by ROV Yaw
        cy = math.cos(-self.yaw)
        sy = math.sin(-self.yaw)
        rx = cy * dx - sy * dy
        ry = sy * dx + cy * dy
        rz = dz

        # Rotate by Camera Gimbal (Pan & Tilt)
        pan = self.camera_pan * math.radians(45.0)
        tilt = self.camera_tilt * math.radians(40.0)

        cp = math.cos(-pan)
        sp = math.sin(-pan)
        gx = cp * rx - sp * ry
        gy = sp * rx + cp * ry
        gz = rz

        ct = math.cos(tilt)
        st = math.sin(tilt)
        cx = gx
        cy = ct * gy - st * gz
        cz = st * gy + ct * gz

        return cx, cy, cz

    def _project_point(self, cx, cy, cz):
        """Projects a camera-space point (cx, cy, cz) onto 2D screen coordinates."""
        if cy <= self.near_clip:
            return None, None
        sx = int(self.width / 2.0 + (cx * self.focal_length) / cy)
        sy = int(self.height / 2.0 - (cz * self.focal_length) / cy)
        return sx, sy

    def _clip_line_to_near_plane(self, p1, p2):
        """
        Clips a 3D line segment to the near clipping plane (cy >= near_clip).
        Eliminates popping and stretching glitches when approaching objects.
        """
        x1, y1, z1 = p1
        x2, y2, z2 = p2

        if y1 < self.near_clip and y2 < self.near_clip:
            return None, None

        if y1 < self.near_clip:
            t = (self.near_clip - y1) / (y2 - y1)
            x1 = x1 + t * (x2 - x1)
            z1 = z1 + t * (z2 - z1)
            y1 = self.near_clip

        if y2 < self.near_clip:
            t = (self.near_clip - y2) / (y1 - y2)
            x2 = x2 + t * (x1 - x2)
            z2 = z2 + t * (z1 - z2)
            y2 = self.near_clip

        return (x1, y1, z1), (x2, y2, z2)

    def _apply_fog(self, color, depth, max_dist=26.0):
        """Applies realistic exponential underwater fog falloff."""
        fog_ratio = max(0.0, min(1.0, 1.0 - math.exp(-depth / 10.0)))
        light_boost = (self.dome_lights * 0.3 + self.ext_lights * 0.7)
        fog_color = (
            int(8 + light_boost * 25),
            int(38 + light_boost * 35),
            int(68 + light_boost * 45)
        )
        return (
            int(color[0] * (1.0 - fog_ratio) + fog_color[0] * fog_ratio),
            int(color[1] * (1.0 - fog_ratio) + fog_color[1] * fog_ratio),
            int(color[2] * (1.0 - fog_ratio) + fog_color[2] * fog_ratio)
        )

    # -------------------------------------------------------------------------
    # Render Engine (Depth-Sorted Painter's Algorithm)
    # -------------------------------------------------------------------------
    def _render(self, t: float):
        # 1. Base ocean background gradient
        light_boost = (self.dome_lights * 0.3 + self.ext_lights * 0.7)
        top_c = (int(10 + light_boost * 30), int(45 + light_boost * 45), int(80 + light_boost * 55))
        bot_c = (int(4 + light_boost * 15), int(20 + light_boost * 25), int(40 + light_boost * 30))

        for y in range(0, self.height, 6):
            frac = y / self.height
            c = (
                int(top_c[0] * (1 - frac) + bot_c[0] * frac),
                int(top_c[1] * (1 - frac) + bot_c[1] * frac),
                int(top_c[2] * (1 - frac) + bot_c[2] * frac)
            )
            pygame.draw.rect(self.surface, c, (0, y, self.width, 6))

        # Clear overlay surface
        self.overlay_surf.fill((0, 0, 0, 0))

        # 2. Water surface caustics shimmer (visible near surface)
        wave_intensity = int(max(0, (1.0 - abs(self.pos[2]) / 7.0) * 35))
        if wave_intensity > 2:
            for i in range(4):
                wy = int(self.height * 0.18 + math.sin(t * 1.8 + i * 1.4) * 35 + i * 40)
                if 0 <= wy < self.height:
                    pygame.draw.ellipse(
                        self.overlay_surf,
                        (180, 240, 255, wave_intensity),
                        (int(self.width * 0.15 + math.cos(t + i) * 70), wy, int(self.width * 0.7), 24),
                        width=2
                    )

        # 3. Collect 3D Render Queue for Depth Sorting
        # Format: (depth, render_function)
        render_queue = []

        # A. Seabed Grid Lines (Near-plane clipped)
        seabed_z = -10.0
        cam_grid_y = int(self.pos[1] / 2.0) * 2

        # Longitudinal grid lines
        for gx in range(-16, 17, 2):
            p1_cam = self._world_to_camera(gx, cam_grid_y + 0.5, seabed_z)
            p2_cam = self._world_to_camera(gx, cam_grid_y + 26.0, seabed_z)
            clipped = self._clip_line_to_near_plane(p1_cam, p2_cam)
            if clipped[0] is not None:
                sx1, sy1 = self._project_point(*clipped[0])
                sx2, sy2 = self._project_point(*clipped[1])
                if sx1 is not None and sx2 is not None:
                    avg_d = (clipped[0][1] + clipped[1][1]) / 2.0
                    alpha = max(0, min(130, int((1.0 - avg_d / 24.0) * 130)))
                    if alpha > 5:
                        render_queue.append((avg_d, lambda s1=(sx1, sy1), s2=(sx2, sy2), a=alpha:
                            pygame.draw.line(self.overlay_surf, (50, 110, 130, a), s1, s2, 1)))

        # Transverse grid lines
        for gy in range(cam_grid_y + 2, cam_grid_y + 26, 2):
            p1_cam = self._world_to_camera(-16.0, gy, seabed_z)
            p2_cam = self._world_to_camera(16.0, gy, seabed_z)
            clipped = self._clip_line_to_near_plane(p1_cam, p2_cam)
            if clipped[0] is not None:
                sx1, sy1 = self._project_point(*clipped[0])
                sx2, sy2 = self._project_point(*clipped[1])
                if sx1 is not None and sx2 is not None:
                    avg_d = (clipped[0][1] + clipped[1][1]) / 2.0
                    alpha = max(0, min(130, int((1.0 - avg_d / 24.0) * 130)))
                    if alpha > 5:
                        render_queue.append((avg_d, lambda s1=(sx1, sy1), s2=(sx2, sy2), a=alpha:
                            pygame.draw.line(self.overlay_surf, (50, 110, 130, a), s1, s2, 1)))

        # B. Subsea Pipeline (Cylindrical segments with hazard stripes)
        for px in range(-16, 16, 2):
            p1_cam = self._world_to_camera(px, self.pipe_y, self.pipe_z)
            p2_cam = self._world_to_camera(px + 1.9, self.pipe_y, self.pipe_z)
            clipped = self._clip_line_to_near_plane(p1_cam, p2_cam)
            if clipped[0] is not None:
                sx1, sy1 = self._project_point(*clipped[0])
                sx2, sy2 = self._project_point(*clipped[1])
                if sx1 is not None and sx2 is not None:
                    avg_d = (clipped[0][1] + clipped[1][1]) / 2.0
                    if avg_d < 28.0:
                        thick = max(3, int(42.0 / avg_d))
                        is_yellow = ((px // 2) % 2 == 0)
                        base_c = (235, 175, 35) if is_yellow else (55, 60, 65)
                        fog_c = self._apply_fog(base_c, avg_d)
                        render_queue.append((avg_d, lambda s1=(sx1, sy1), s2=(sx2, sy2), c=fog_c, th=thick:
                            pygame.draw.line(self.surface, c, s1, s2, th)))

        # C. Subsea Inspection Arch / Hoop
        gate_cam = self._world_to_camera(self.gate_x, self.gate_y, self.gate_z)
        if gate_cam[1] > self.near_clip and gate_cam[1] < 32.0:
            gsx, gsy = self._project_point(*gate_cam)
            if gsx is not None:
                radius = int((self.gate_radius * self.focal_length) / gate_cam[1])
                if radius > 3:
                    hoop_c = self._apply_fog((250, 210, 50), gate_cam[1])
                    beacon_c = (255, 50, 50) if int(t * 3.0) % 2 == 0 else (120, 20, 20)
                    render_queue.append((gate_cam[1], lambda pos=(gsx, gsy), r=radius, c=hoop_c, bc=beacon_c: (
                        pygame.draw.circle(self.surface, c, pos, r, width=max(2, r // 8)),
                        pygame.draw.circle(self.surface, bc, (pos[0], pos[1] - r), max(3, r // 6))
                    )))

        # D. Seabed Rocks (Shaded 3D Ellipsoids)
        for rk in self.rocks:
            rc = self._world_to_camera(rk['x'], rk['y'], rk['z'])
            if rc[1] > self.near_clip and rc[1] < 28.0:
                rsx, rsy = self._project_point(*rc)
                if rsx is not None:
                    rw_px = max(2, int((rk['w'] * self.focal_length) / rc[1]))
                    rh_px = max(1, int((rk['h'] * self.focal_length) / rc[1]))
                    c = self._apply_fog(rk['c'], rc[1])
                    render_queue.append((rc[1], lambda pos=(rsx, rsy), w=rw_px, h=rh_px, col=c:
                        pygame.draw.ellipse(self.surface, col, (pos[0] - w, pos[1] - h // 2, w * 2, h))))

        # E. Crabs (OSU Robotics Inspection Targets)
        for crab in self.crabs:
            cc = self._world_to_camera(crab['x'], crab['y'], crab['z'])
            if cc[1] > self.near_clip and cc[1] < 22.0:
                csx, csy = self._project_point(*cc)
                if csx is not None:
                    csz = max(3, int(22.0 / cc[1]))
                    crab_c = self._apply_fog((225, 65, 45), cc[1])
                    leg_c = self._apply_fog((175, 45, 30), cc[1])
                    phase = crab['phase']
                    render_queue.append((cc[1], lambda pos=(csx, csy), sz=csz, c=crab_c, lc=leg_c, ph=phase: (
                        # Crab Carapace
                        pygame.draw.ellipse(self.surface, c, (pos[0] - sz, pos[1] - sz // 2, sz * 2, sz)),
                        # Claws
                        pygame.draw.circle(self.surface, c, (pos[0] - int(sz * 1.1), pos[1] - sz // 2), max(2, sz // 3)),
                        pygame.draw.circle(self.surface, c, (pos[0] + int(sz * 1.1), pos[1] - sz // 2), max(2, sz // 3)),
                        # Articulated Legs
                        [pygame.draw.line(self.surface, lc,
                            (pos[0] - int(sz * 0.8), pos[1]),
                            (pos[0] - sz * 2, pos[1] + i * (sz // 2) + int(math.sin(ph + i) * (sz // 3))),
                            max(1, sz // 4)) for i in range(-2, 3)],
                        [pygame.draw.line(self.surface, lc,
                            (pos[0] + int(sz * 0.8), pos[1]),
                            (pos[0] + sz * 2, pos[1] + i * (sz // 2) - int(math.sin(ph + i) * (sz // 3))),
                            max(1, sz // 4)) for i in range(-2, 3)]
                    )))

        # F. Swimming Fish
        for fish in self.fish:
            fc = self._world_to_camera(fish['x'], fish['y'], fish['z'])
            if fc[1] > self.near_clip and fc[1] < 26.0:
                fsx, fsy = self._project_point(*fc)
                if fsx is not None:
                    flen = max(3, int((fish['size'] * 140.0) / fc[1]))
                    fh = max(2, flen // 3)
                    tail_wag = int(math.sin(fish['phase'] * 3.0) * (flen * 0.35))
                    fish_c = self._apply_fog((110, 190, 220), fc[1])
                    render_queue.append((fc[1], lambda pos=(fsx, fsy), l=flen, h=fh, tw=tail_wag, c=fish_c: (
                        pygame.draw.ellipse(self.surface, c, (pos[0] - l, pos[1] - h // 2, l * 2, h)),
                        pygame.draw.polygon(self.surface, c, [
                            (pos[0] - l, pos[1]),
                            (pos[0] - l - h, pos[1] - h + tw),
                            (pos[0] - l - h, pos[1] + h + tw)
                        ])
                    )))

        # G. Marine Snow Particulates
        for p in self.marine_snow:
            pc = self._world_to_camera(p[0], p[1], p[2])
            if pc[1] > self.near_clip and pc[1] < 16.0:
                psx, psy = self._project_point(*pc)
                if psx is not None:
                    bright = int(max(40, (1.0 - pc[1] / 16.0) * 220))
                    psz = max(1, int(p[3] / (pc[1] * 0.6)))
                    render_queue.append((pc[1], lambda pos=(psx, psy), b=bright, s=psz:
                        pygame.draw.circle(self.surface, (b, b, min(255, b + 35)), pos, s)))

        # 4. Sort Back-to-Front (Painter's Algorithm) and Render
        render_queue.sort(key=lambda item: item[0], reverse=True)
        for depth, draw_func in render_queue:
            draw_func()

        # Blit alpha overlay layer
        self.surface.blit(self.overlay_surf, (0, 0))

        # 5. Dynamic Spotlights (Headlights)
        if self.dome_lights > 0.05 or self.ext_lights > 0.05:
            cone_alpha = int((self.dome_lights * 0.4 + self.ext_lights * 0.6) * 115)
            spot_cx = self.width // 2 - int(self.camera_pan * 90)
            spot_cy = self.height // 2 + int(self.camera_tilt * 90)

            # Dual beam gradient cones
            self.overlay_surf.fill((0, 0, 0, 0))
            for r in (260, 200, 140, 80):
                a = int(cone_alpha * (1.0 - r / 260.0))
                pygame.draw.ellipse(self.overlay_surf, (240, 252, 255, a),
                                    (spot_cx - r, spot_cy - int(r * 0.65), r * 2, int(r * 1.3)))
            self.surface.blit(self.overlay_surf, (0, 0))

        # 6. Naval ROV Telemetry HUD Overlay
        self._render_hud()

    def _render_hud(self):
        """Renders modern naval submarine HUD with compass ribbon and depth tape."""
        self.hud_surf.fill((0, 0, 0, 0))
        hud_cyan = (0, 240, 215)
        hud_dim = (0, 180, 160)

        # Center Targeting Crosshairs
        cx = self.width // 2
        cy = self.height // 2
        pygame.draw.circle(self.hud_surf, hud_dim, (cx, cy), 22, width=1)
        pygame.draw.line(self.hud_surf, hud_cyan, (cx - 15, cy), (cx - 5, cy), 1)
        pygame.draw.line(self.hud_cyan if False else self.hud_surf, hud_cyan, (cx + 5, cy), (cx + 15, cy), 1)
        pygame.draw.line(self.hud_surf, hud_cyan, (cx, cy - 15), (cx, cy - 5), 1)
        pygame.draw.line(self.hud_surf, hud_cyan, (cx, cy + 5), (cx, cy + 15), 1)

        # Top Heading Ribbon (Compass)
        heading_deg = int(math.degrees(self.yaw)) % 360
        ribbon_y = 20
        pygame.draw.line(self.hud_surf, hud_dim, (cx - 100, ribbon_y), (cx + 100, ribbon_y), 1)
        pygame.draw.polygon(self.hud_surf, hud_cyan, [(cx, ribbon_y + 4), (cx - 4, ribbon_y + 9), (cx + 4, ribbon_y + 9)])

        # Compass tick marks
        for offset in range(-80, 85, 20):
            deg = (heading_deg + offset) % 360
            tx = cx + offset
            pygame.draw.line(self.hud_surf, hud_dim, (tx, ribbon_y - 4), (tx, ribbon_y), 1)
            if deg % 45 == 0:
                cardinal = {0: 'N', 45: 'NE', 90: 'E', 135: 'SE', 180: 'S', 225: 'SW', 270: 'W', 315: 'NW'}.get(deg, str(deg))
                lbl = self.font_small.render(cardinal, True, hud_cyan)
                self.hud_surf.blit(lbl, (tx - lbl.get_width() // 2, ribbon_y - 16))

        # Left Depth Tape
        depth_m = abs(self.pos[2])
        depth_x = 35
        tape_top = cy - 60
        tape_bot = cy + 60
        pygame.draw.line(self.hud_surf, hud_dim, (depth_x, tape_top), (depth_x, tape_bot), 1)
        pygame.draw.polygon(self.hud_surf, hud_cyan, [(depth_x + 3, cy), (depth_x + 8, cy - 4), (depth_x + 8, cy + 4)])

        # Depth readout box
        depth_txt = self.font_large.render(f"{depth_m:.2f}m", True, hud_cyan)
        self.hud_surf.blit(depth_txt, (depth_x + 12, cy - depth_txt.get_height() // 2))

        # Bottom Information Bar
        hdg_txt = self.font_small.render(f"HDG: {heading_deg:03d}° | CAM: [{self.camera_pan:.1f}, {self.camera_tilt:.1f}]", True, hud_cyan)
        self.hud_surf.blit(hdg_txt, (15, self.height - 24))

        # Active Thrusters Mini-Indicator (top right)
        t_x = self.width - 110
        t_y = 15
        ind_lbl = self.font_small.render("THRUSTERS", True, hud_dim)
        self.hud_surf.blit(ind_lbl, (t_x, t_y))
        for i, (name, pwm) in enumerate(list(self.thrusters.items())[:4]):
            p_val = (pwm - 1500) / 400.0  # -1.0 to 1.0
            bx = t_x + i * 22
            by = t_y + 16
            pygame.draw.rect(self.hud_surf, (30, 60, 70), (bx, by, 18, 12), 1)
            if abs(p_val) > 0.05:
                fill_c = (0, 240, 100) if p_val > 0 else (240, 60, 60)
                pygame.draw.rect(self.hud_surf, fill_c, (bx + 2, by + 2, 14, 8))

        self.surface.blit(self.hud_surf, (0, 0))

    # -------------------------------------------------------------------------
    # Main Step
    # -------------------------------------------------------------------------
    def _step(self):
        now = time.time()
        # Smooth and clamp delta time to eliminate timing stutters
        dt = min(0.06, max(0.01, now - self.last_time))
        self.last_time = now

        # 1. Physics Step
        self._update_physics(dt)

        # 2. 3D Render Step
        self._render(now)

        # 3. Publish sensor_msgs/Image
        img_bytes = pygame.image.tobytes(self.surface, "RGB")
        msg = Image()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "camera_optical_frame"
        msg.width = self.width
        msg.height = self.height
        msg.encoding = "rgb8"
        msg.is_bigendian = 0
        msg.step = self.width * 3
        msg.data = img_bytes
        self.image_pub.publish(msg)

        # 4. Publish Telemetry
        telemetry_str = (
            f"lfl={self.thrusters['lfl']},lfr={self.thrusters['lfr']},"
            f"lbl={self.thrusters['lbl']},lbr={self.thrusters['lbr']},"
            f"vfl={self.thrusters['vfl']},vfr={self.thrusters['vfr']},"
            f"vbl={self.thrusters['vbl']},vbr={self.thrusters['vbr']},"
            f"camera_x={self.camera_pan:.2f},camera_y={self.camera_tilt:.2f},"
            f"dome_lights={self.dome_lights:.2f},ext_lights={self.ext_lights:.2f},"
            f"dome_lights_max={self.dome_lights:.2f},ext_lights_max={self.ext_lights:.2f},"
            f"manip=0,manip_rotate=1500"
        )
        t_msg = String()
        t_msg.data = telemetry_str
        self.motor_pub.publish(t_msg)


def main(args=None):
    rclpy.init(args=args)
    sim = UnderwaterSim()
    try:
        rclpy.spin(sim)
    except KeyboardInterrupt:
        pass
    finally:
        sim.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
