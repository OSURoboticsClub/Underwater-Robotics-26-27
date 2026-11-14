class_name SimROV
extends CharacterBody3D

## 3D Simulated ROV with 6-DOF Hydrodynamics, Camera Gimbal, Headlights,
## and Training Obstacle Course Driver HUD & Collision Detection.

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
@onready var hud_label: Label3D = $GimbalPan/GimbalTilt/Camera3D/HudLabel

# Motion State
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

# Obstacle Course & Driving Practice Metrics
var collision_count: int = 0
var _was_colliding: bool = false
var _collision_flash_timer: float = 0.0

var course_started: bool = false
var course_completed: bool = false
var course_timer: float = 0.0
var gates_cleared: int = 0
const TOTAL_GATES: int = 3

var banner_text: String = ""
var banner_timer: float = 0.0


func _ready() -> void:
	SignalBus.incoming_data.connect(_on_incoming_telemetry)
	SignalBus.outgoing_data.connect(_on_outgoing_data)

	# Connect all gates in scene tree
	await get_tree().process_frame
	_connect_course_gates()
	reset_course()


func _connect_course_gates() -> void:
	var gates = get_tree().get_nodes_in_group("gates")
	for g in gates:
		if g is SimGate and not g.gate_passed.is_connected(_on_gate_passed):
			g.gate_passed.connect(_on_gate_passed)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_F:
			spotlight_energy = 0.0 if spotlight_energy > 0.1 else 1.0
		elif event.keycode == KEY_R:
			reset_course()


func reset_course() -> void:
	global_position = Vector3(0.0, -3.5, 0.0)
	rotation = Vector3.ZERO
	velocity = Vector3.ZERO
	target_vel = Vector3.ZERO
	target_yaw_rate = 0.0
	camera_pan_angle = 0.0
	camera_tilt_angle = 0.0

	collision_count = 0
	_was_colliding = false
	_collision_flash_timer = 0.0

	course_started = false
	course_completed = false
	course_timer = 0.0
	gates_cleared = 0

	banner_text = "PRACTICE COURSE: FLY FORWARD TO START"
	banner_timer = 3.5

	var gates = get_tree().get_nodes_in_group("gates")
	for g in gates:
		if g.has_method("reset_gate"):
			g.reset_gate()


func _on_gate_passed(gate_id: int, gate_name: String) -> void:
	gates_cleared = max(gates_cleared, gate_id)
	banner_text = "%s CLEARED!" % gate_name.to_upper()
	banner_timer = 2.5

	if gates_cleared >= TOTAL_GATES:
		course_completed = true
		banner_text = "FINISH! Time: %.1fs | Hits: %d | [R] to Retry" % [course_timer, collision_count]
		banner_timer = 12.0


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

	# 5. Move with solid collision detection
	move_and_slide()

	# 6. Check for physical obstacle collisions (bump counter)
	var num_collisions = get_slide_collision_count()
	if num_collisions > 0:
		if not _was_colliding:
			collision_count += 1
			_collision_flash_timer = 0.55
			_was_colliding = true
	else:
		_was_colliding = false

	# 7. Clamp depth (water surface Y=0.0, seabed Y=-9.6)
	global_position.y = clampf(global_position.y, -9.6, -0.3)

	# 8. Start and advance course timer
	if not course_started and (global_position.z < -2.0 or velocity.length() > 0.4):
		course_started = true

	if course_started and not course_completed:
		course_timer += delta

	# 9. Update camera gimbal smoothly
	gimbal_pan.rotation.y = lerpf(gimbal_pan.rotation.y, camera_pan_angle, delta * 8.0)
	gimbal_tilt.rotation.x = lerpf(gimbal_tilt.rotation.x, camera_tilt_angle, delta * 8.0)

	# 10. Update headlights
	var energy = spotlight_energy * 3.5
	light_left.light_energy = lerpf(light_left.light_energy, energy, delta * 10.0)
	light_right.light_energy = lerpf(light_right.light_energy, energy, delta * 10.0)

	# 11. Update Driver Training HUD
	_update_hud(delta)

	# 12. Feed live thruster telemetry back to Groundstation UI
	_publish_telemetry()


func _update_hud(delta: float) -> void:
	if hud_label == null:
		return

	if _collision_flash_timer > 0.0:
		_collision_flash_timer -= delta
		hud_label.modulate = Color(1.0, 0.2, 0.2, 1.0) # Flash Red
		hud_label.text = "*** COLLISION DETECTED *** (Hits: %d)" % collision_count
		return

	if banner_timer > 0.0:
		banner_timer -= delta
		hud_label.modulate = Color(0.2, 1.0, 0.4, 1.0) # Bright Green
		hud_label.text = banner_text
		return

	hud_label.modulate = Color(0.85, 0.95, 1.0, 0.9)
	var depth = absf(global_position.y)
	var speed = velocity.length()

	if course_completed:
		hud_label.text = "COURSE COMPLETE! Time: %.1fs | Hits: %d | [R] to Restart" % [course_timer, collision_count]
	else:
		hud_label.text = "Gate: %d/%d | Hits: %d | Time: %.1fs | Depth: %.1fm | Spd: %.1fm/s" % [
			gates_cleared, TOTAL_GATES, collision_count, course_timer, depth, speed
		]


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

	# Gamepad sticks & triggers (if connected)
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

		# Controller shortcut: Start or Back button resets course
		if Input.is_joy_button_pressed(0, JOY_BUTTON_START) or Input.is_joy_button_pressed(0, JOY_BUTTON_BACK):
			reset_course()

	# Clamp commands
	surge = clampf(surge, -1.0, 1.0)
	sway = clampf(sway, -1.0, 1.0)
	heave = clampf(heave, -1.0, 1.0)
	yaw = clampf(yaw, -1.0, 1.0)

	# Target body velocity
	target_vel = Vector3(sway * sway_speed, heave * heave_speed, surge * surge_speed)
	target_yaw_rate = yaw * yaw_speed

	# Calculate 8-Thruster PWMs for UI displays
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
