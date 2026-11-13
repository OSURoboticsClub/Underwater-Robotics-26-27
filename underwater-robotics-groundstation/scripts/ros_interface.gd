extends RosNode

var key_states_publisher: RosPublisher
var servo_publisher: RosPublisher

var motor_subscription: RosSubscription
var servo_subscription: RosSubscription
var video_subscription: RosSubscription


func _ready() -> void:
	await get_tree().process_frame

	# Subscriptions
	servo_subscription = create_subscription(
		"std_msgs/msg/String",
		"/servo_command",
		_on_message_received,
		10
	)
	if servo_subscription == null:
		SignalBus.error.emit("Failed to subscribe to /servo_command")

	video_subscription = create_subscription(
		"sensor_msgs/msg/Image",
		"/image_raw",
		_handle_image,
		RosQoSProfile.sensor_data()
	)
	if video_subscription == null:
		SignalBus.error.emit("Failed to subscribe to /image_raw")

	motor_subscription = create_subscription(
		"std_msgs/msg/String",
		"/motor_command",
		_on_message_received,
		10
	)
	if motor_subscription == null:
		SignalBus.error.emit("Failed to subscribe to /motor_command")

	# Publishers
	key_states_publisher = create_publisher(
		"std_msgs/msg/String",
		"/key_states",
		10
	)
	if key_states_publisher == null:
		SignalBus.error.emit("Failed to create publisher for /key_states")

	servo_publisher = create_publisher(
		"std_msgs/msg/String",
		"/servo_command",
		10
	)
	if servo_publisher == null:
		SignalBus.error.emit("Failed to create publisher for /servo_command")

	SignalBus.outgoing_data.connect(_publish_data)


func _process(_delta: float) -> void:
	spin_some()
	_handle_keyboard_inputs()


func _handle_keyboard_inputs() -> void:
	var inputs: Array[String] = []

	# Action mappings
	if Input.is_action_pressed("up"):
		inputs.append("UP")
	if Input.is_action_pressed("down"):
		inputs.append("DOWN")
	if Input.is_action_pressed("left"):
		inputs.append("LEFT")
	if Input.is_action_pressed("right"):
		inputs.append("RIGHT")
	if Input.is_action_pressed("dome_lights"):
		inputs.append("D")
	if Input.is_action_pressed("exterior_lights"):
		inputs.append("E")
	if Input.is_action_pressed("camera"):
		inputs.append("C")
	if Input.is_action_pressed("reset"):
		inputs.append("BACKSPACE")
	if Input.is_action_pressed("x"):
		inputs.append("X")
	if Input.is_action_pressed("y"):
		inputs.append("Y")

	# ROV Movement Keys (WASD + Q/E + Space/Shift)
	if Input.is_key_pressed(KEY_W):
		inputs.append("W")
	if Input.is_key_pressed(KEY_S):
		inputs.append("S")
	if Input.is_key_pressed(KEY_A):
		inputs.append("A")
	if Input.is_key_pressed(KEY_D):
		inputs.append("D")
	if Input.is_key_pressed(KEY_Q):
		inputs.append("Q")
	if Input.is_key_pressed(KEY_E):
		inputs.append("E")
	if Input.is_key_pressed(KEY_SPACE):
		inputs.append("SPACE")
	if Input.is_key_pressed(KEY_SHIFT):
		inputs.append("SHIFT")

	# Gamepad Joysticks (if connected)
	if Input.get_connected_joypads().size() > 0:
		var lx = Input.get_joy_axis(0, JOY_AXIS_LEFT_X)
		var ly = Input.get_joy_axis(0, JOY_AXIS_LEFT_Y)
		var rx = Input.get_joy_axis(0, JOY_AXIS_RIGHT_X)
		var ry = Input.get_joy_axis(0, JOY_AXIS_RIGHT_Y)
		var lt = Input.get_joy_axis(0, JOY_AXIS_TRIGGER_LEFT)
		var rt = Input.get_joy_axis(0, JOY_AXIS_TRIGGER_RIGHT)

		var deadzone = 0.15
		if abs(lx) > deadzone:
			inputs.append("JOY_LX:" + str(snappedf(lx, 0.01)))
		if abs(ly) > deadzone:
			inputs.append("JOY_LY:" + str(snappedf(ly, 0.01)))
		if abs(rx) > deadzone:
			inputs.append("JOY_RX:" + str(snappedf(rx, 0.01)))
		if abs(ry) > deadzone:
			inputs.append("JOY_RY:" + str(snappedf(ry, 0.01)))
		if lt > 0.1:
			inputs.append("JOY_LT:" + str(snappedf(lt, 0.01)))
		if rt > 0.1:
			inputs.append("JOY_RT:" + str(snappedf(rt, 0.01)))

	# Publish inputs if active
	if inputs.size() > 0 and key_states_publisher != null:
		var msg = RosMsg.create("std_msgs/msg/String")
		msg.data = ",".join(inputs)
		key_states_publisher.publish(msg)


func _on_message_received(msg) -> void:
	if msg == null or msg.data.is_empty():
		return

	var data: Dictionary[String, Variant] = {}
	var pieces = msg.data.split(",")
	for p in pieces:
		var parts = p.split("=")
		if parts.size() == 2:
			data[parts[0]] = parts[1]

	if not data.is_empty():
		SignalBus.incoming_data.emit(data)


func _handle_image(msg) -> void:
	if msg != null:
		SignalBus.incoming_video.emit(msg)


func _publish_data(pub_name: String, data: Dictionary[String, Variant]) -> void:
	if pub_name == "servo" and servo_publisher != null:
		var output: Array[String] = []
		for key in data:
			output.append(key + ":" + str(data[key]))
		var msg = RosMsg.create("std_msgs/msg/String")
		msg.data = ",".join(output)
		servo_publisher.publish(msg)
