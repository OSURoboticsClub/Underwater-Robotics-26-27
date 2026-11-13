class_name SimROV
extends CharacterBody3D

## 3D Simulated ROV with 6-DOF Hydrodynamics, Camera Gimbal, and Spotlights

# Movement parameters
@export var surge_speed: float = 3.2
@export var sway_speed: float = 2.4
@export var heave_speed: float = 2.0
@export var yaw_speed: float = 2.0
@export var drag: float = 3.5

# Nodes
@onready var gimbal_pan: Node3D = $GimbalPan
@onready var gimbal_tilt: Node3D = $GimbalPan/GimbalTilt
@onready var camera_3d: Camera3D = $GimbalPan/GimbalTilt/Camera3D
@onready var light_left: SpotLight3D = $GimbalPan/GimbalTilt/LightLeft
@onready var light_right: SpotLight3D = $GimbalPan/GimbalTilt/LightRight

# State
var target_vel: Vector3 = Vector3.ZERO
var target_yaw_rate: float = 0.0

var camera_pan_angle: float = 0.0
var camera_tilt_angle: float = 0.0
var spotlight_energy: float = 0.0

var thrusters: Dictionary = {
	"lfl": 1500, "lfr": 1500, "lbl": 1500, "lbr": 1500,
	"vfl": 1500, "vfr": 1500, "vbl": 1500, "vbr": 1500
}


var _internal_update: bool = false


func _ready() -> void:
	SignalBus.incoming_data.connect(_on_incoming_telemetry)
	SignalBus.outgoing_data.connect(_on_outgoing_data)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_F:
			spotlight_energy = 0.0 if spotlight_energy > 0.1 else 1.0


func _physics_process(delta: float) -> void:
	# 1. Read Inputs (Gamepad & Keyboard)
	_process_inputs(delta)

	# 2. Smoothly rotate ROV heading (Yaw)
	rotate_y(target_yaw_rate * delta)

	# 3. Transform body velocity to world coordinates
	var body_vel = transform.basis * target_vel

	# 4. Apply smooth acceleration and hydrodynamic drag
	velocity = velocity.lerp(body_vel, delta * 4.5)
	velocity = velocity.lerp(Vector3.ZERO, delta * 0.8)

	# 5. Move with collision detection (stops at seabed or structures)
	move_and_slide()

	# 6. Clamp depth (water surface Y=0.0, seabed Y=-9.6)
	global_position.y = clampf(global_position.y, -9.6, -0.3)

	# 7. Update camera gimbal smoothly
	gimbal_pan.rotation.y = lerpf(gimbal_pan.rotation.y, camera_pan_angle, delta * 8.0)
	gimbal_tilt.rotation.x = lerpf(gimbal_tilt.rotation.x, camera_tilt_angle, delta * 8.0)

	# 8. Update headlights
	var energy = spotlight_energy * 3.5
	light_left.light_energy = lerpf(light_left.light_energy, energy, delta * 10.0)
	light_right.light_energy = lerpf(light_right.light_energy, energy, delta * 10.0)

	# 9. Feed live thruster telemetry back to Groundstation UI
	_publish_telemetry()


func _process_inputs(delta: float) -> void:
	var surge := 0.0
	var sway := 0.0
	var heave := 0.0
	var yaw := 0.0

	# Keyboard Movement (WASD + Q/E + Space/Shift)
	if Input.is_key_pressed(KEY_W):
		surge -= 1.0  # -Z is forward in Godot
	if Input.is_key_pressed(KEY_S):
		surge += 1.0
	if Input.is_key_pressed(KEY_D):
		sway += 1.0   # +X is right
	if Input.is_key_pressed(KEY_A):
		sway -= 1.0
	if Input.is_key_pressed(KEY_E):
		yaw -= 1.0   # Turn right
	if Input.is_key_pressed(KEY_Q):
		yaw += 1.0   # Turn left
	if Input.is_key_pressed(KEY_SPACE):
		heave += 1.0 # Surface (+Y)
	if Input.is_key_pressed(KEY_SHIFT):
		heave -= 1.0 # Dive (-Y)

	# Camera Gimbal Keyboard controls (I/K for tilt, J/L for pan)
	if Input.is_key_pressed(KEY_I):
		camera_tilt_angle = clampf(camera_tilt_angle + 1.2 * delta, -deg_to_rad(40), deg_to_rad(40))
	if Input.is_key_pressed(KEY_K):
		camera_tilt_angle = clampf(camera_tilt_angle - 1.2 * delta, -deg_to_rad(40), deg_to_rad(40))
	if Input.is_key_pressed(KEY_J):
		camera_pan_angle = clampf(camera_pan_angle + 1.2 * delta, -deg_to_rad(45), deg_to_rad(45))
	if Input.is_key_pressed(KEY_L):
		camera_pan_angle = clampf(camera_pan_angle - 1.2 * delta, -deg_to_rad(45), deg_to_rad(45))

	# Gamepad sticks (if connected)
	if Input.get_connected_joypads().size() > 0:
		var lx = Input.get_joy_axis(0, JOY_AXIS_LEFT_X)
		var ly = Input.get_joy_axis(0, JOY_AXIS_LEFT_Y)
		var rx = Input.get_joy_axis(0, JOY_AXIS_RIGHT_X)
		var rt = Input.get_joy_axis(0, JOY_AXIS_TRIGGER_RIGHT)
		var lt = Input.get_joy_axis(0, JOY_AXIS_TRIGGER_LEFT)

		if abs(ly) > 0.15:
			surge += ly
		if abs(lx) > 0.15:
			sway += lx
		if abs(rx) > 0.15:
			yaw -= rx
		if rt > 0.1:
			heave += rt
		if lt > 0.1:
			heave -= lt

	# Clamp commands
	surge = clampf(surge, -1.0, 1.0)
	sway = clampf(sway, -1.0, 1.0)
	heave = clampf(heave, -1.0, 1.0)
	yaw = clampf(yaw, -1.0, 1.0)

	# Target body velocity
	target_vel = Vector3(sway * sway_speed, heave * heave_speed, surge * surge_speed)
	target_yaw_rate = yaw * yaw_speed

	# Calculate 8-Thruster PWMs for UI displays
	# (In Godot: forward is -surge, so cmd_surge = -surge)
	var cmd_surge = -surge
	thrusters["lfl"] = _clamp_pwm(1500 + (cmd_surge - sway - yaw) * 350.0)
	thrusters["lfr"] = _clamp_pwm(1500 + (cmd_surge + sway + yaw) * 350.0)
	thrusters["lbl"] = _clamp_pwm(1500 + (cmd_surge + sway - yaw) * 350.0)
	thrusters["lbr"] = _clamp_pwm(1500 + (cmd_surge - sway + yaw) * 350.0)

	thrusters["vfl"] = _clamp_pwm(1500 + heave * 350.0)
	thrusters["vfr"] = _clamp_pwm(1500 + heave * 350.0)
	thrusters["vbl"] = _clamp_pwm(1500 + heave * 350.0)
	thrusters["vbr"] = _clamp_pwm(1500 + heave * 350.0)


func _clamp_pwm(val: float) -> int:
	return int(clampf(val, 1100.0, 1900.0))


func _on_outgoing_data(_pub_name: String, data: Dictionary[String, Variant]) -> void:
	if data.has("ext_lights"):
		spotlight_energy = float(data["ext_lights"])
	if data.has("ext_lights_max"):
		spotlight_energy = float(data["ext_lights_max"])


func _on_incoming_telemetry(data: Dictionary[String, Variant]) -> void:
	if _internal_update:
		return
	if data.has("camera_x"):
		camera_pan_angle = -float(data["camera_x"]) * deg_to_rad(45.0)
	if data.has("camera_y"):
		camera_tilt_angle = float(data["camera_y"]) * deg_to_rad(40.0)
	if data.has("ext_lights_max"):
		spotlight_energy = float(data["ext_lights_max"])
	elif data.has("dome_lights_max"):
		spotlight_energy = float(data["dome_lights_max"])


func _publish_telemetry() -> void:
	_internal_update = true
	var telem: Dictionary[String, Variant] = {}
	for k in thrusters:
		telem[k] = str(thrusters[k])
	telem["camera_x"] = str(snappedf(-rad_to_deg(camera_pan_angle) / 45.0, 0.01))
	telem["camera_y"] = str(snappedf(rad_to_deg(camera_tilt_angle) / 40.0, 0.01))
	telem["ext_lights_max"] = str(snappedf(spotlight_energy, 0.01))
	SignalBus.incoming_data.emit(telem)
	_internal_update = false
