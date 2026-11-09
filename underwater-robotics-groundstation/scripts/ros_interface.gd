extends RosNode

var key_states_publisher: RosPublisher
var servo_publisher: RosPublisher

var motor_subscription: RosSubscription
var servo_subscription: RosSubscription
var joy_servo_subscription: RosSubscription
var video_subscription: RosSubscription

var last_physics_time_usec: int = 0


func _ready():
	await get_tree().process_frame

	# Create Subscriptions
	servo_subscription = create_subscription(
		"std_msgs/msg/String",
		"/servo_command",
		_on_message_received,
		10
	)
	if servo_subscription == null:
		SignalBus.error.emit("Failed to create subscription to '/servo_command'")
	else:
		print("Subscription created: ", servo_subscription)
	
	"""joy_servo_subscription = create_subscription(
		"std_msgs/msg/String",
		"/servo_command",
		_on_message_received,
		10
	)
	if joy_servo_subscription == null:
		SignalBus.error.emit("Failed to create subscription to '/servo_command'")
	else:
		print("Subscription created: ", joy_servo_subscription)"""
		
	
	video_subscription = create_subscription(
		"sensor_msgs/msg/Image",
		"/image_raw",
		_handle_image,
		RosQoSProfile.sensor_data()
	)
	if video_subscription == null:
		SignalBus.error.emit("Failed to create subscription to '/image_raw'")
	else:
		print("Subscription created: ", video_subscription)
	
	
	motor_subscription = create_subscription(
		"std_msgs/msg/String",
		"/motor_command",
		_on_message_received,
		10
	)
	if motor_subscription == null:
		SignalBus.error.emit("Failed to create subscription to '/motor_command'")
	else:
		print("Subscription created: ", motor_subscription)
	
	
	# Create Publishers
	key_states_publisher = create_publisher(
		"std_msgs/msg/String",
		"/key_states",
		10
	)
	if key_states_publisher == null:
		SignalBus.error.emit("Failed to create publisher to '/key_states'")
	else:
		print("Publisher created: ", key_states_publisher)
	
	servo_publisher = create_publisher( #TODO: This needs to actually go to /gound/joy - joy_to_servo
		"std_msgs/msg/String",
		"/servo_command",
		10
	)
	if servo_subscription == null:
		SignalBus.error.emit("Failed to create publisher to '/servo_command'")
	else:
		print("Publisher created: ", servo_subscription)
	
	SignalBus.outgoing_data.connect(_publish_data)



func _process(_delta: float) -> void:
	#var now := Time.get_ticks_usec()

	"""if last_physics_time_usec != 0:
		var interval_ms := (
			now - last_physics_time_usec
		) / 1000.0

		if interval_ms > 30.0:
			print("Physics interval: ", interval_ms, " ms")

	last_physics_time_usec = now

	var spin_start_usec := Time.get_ticks_usec()"""
	spin_some()
	"""var spin_duration_ms := (
		Time.get_ticks_usec() - spin_start_usec
	) / 1000.0"""

	#if spin_duration_ms > 5.0:
	#	print("spin_some duration: ", spin_duration_ms, " ms")

	if Input.is_key_pressed(KEY_P):
		SignalBus.error.emit("New Test Error")
	
	# Get inputs and publish them to appropriate topics
	_handle_keyboard_inputs()

func _handle_keyboard_inputs() -> void:
	var inputs = []
	
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
	
	# Reset camera position
	if Input.is_action_pressed("reset"):
		inputs.append("BACKSPACE")
	if Input.is_action_pressed("x"):
		inputs.append("X")
	if Input.is_action_pressed("y"):
		inputs.append("Y")

	
	# Send imputs if there are any
	if inputs.size() > 0:
		var msg = RosMsg.create("std_msgs/msg/String")
		msg.data = ",".join(inputs)
		key_states_publisher.publish(msg)
	#list of keys the are used in other nodes:
	# C - camera
	# D - dome lights
	# E - exterior lights
	# UP - camera up
	# DOWN - camera down
	# LEFT - camera left
	# RIGHT - camera right
	# BACKSPACE
	# X
	# Y


func _on_message_received(msg):
	#print("RECEIVED MESSAGE: ", msg.data)
	var data: Dictionary[String,Variant] = {}
	var pieces_of_data = msg.data.split(",")
	for d in pieces_of_data:
		var data_parts = d.split("=")
		#print("data_parts: " + str(data_parts))
		data[data_parts.get(0)] = data_parts.get(1)
	if data != {}:
		SignalBus.incoming_data.emit(data)


func _handle_image(msg) -> void:
	SignalBus.incoming_video.emit(msg)


func _publish_data(pub_name: String, data: Dictionary[String, Variant]):
	if pub_name == "servo":
		var output = []
		for key in data:
			output.append(key + ":" + str(data[key]))
		var msg = RosMsg.create("std_msgs/msg/String")
		msg.data = ",".join(output)
		servo_publisher.publish(msg)
	pass
