extends RosNode

# Publisher nodes
var key_states_publisher: RosPublisher
var servo_publisher: RosPublisher
var joy_servo_publisher: RosPublisher

# Subscriber nodes
var motor_subscription: RosSubscription
var servo_subscription: RosSubscription
var joy_servo_subscription: RosSubscription
var video_subscription: RosSubscription


func _ready():
	await get_tree().process_frame

	# Create Subscriptions
	servo_subscription = create_subscription(
		"std_msgs/msg/String",
		Global.topic_mappings["/servo_command"],
		_on_message_received,
		10
	)
	if servo_subscription == null:
		SignalBus.error.emit("Failed to create subscription to '" +Global.topic_mappings["/servo_command"]+"'")
	else:
		print("Subscription created: ", servo_subscription)
	
	joy_servo_publisher = create_publisher(
		"sensor_msgs/msg/Joy",
		Global.topic_mappings["/joy"],
		10
	)
	if joy_servo_publisher == null:
		SignalBus.error.emit("Failed to create subscription to '"+Global.topic_mappings["/joy"]+"'")
	else:
		print("Subscription created: ", joy_servo_publisher)
	
	video_subscription = create_subscription(
		"sensor_msgs/msg/Image",
		Global.topic_mappings["/image_raw"],
		_handle_image,
		RosQoSProfile.sensor_data()
	)
	if video_subscription == null:
		SignalBus.error.emit("Failed to create subscription to '" + Global.topic_remappings["image_raw"]+"'")
	else:
		print("Subscription created: ", video_subscription)
	
	motor_subscription = create_subscription(
		"std_msgs/msg/String",
		Global.topic_mappings["/motor_command"],
		_on_message_received,
		10
	)
	if motor_subscription == null:
		SignalBus.error.emit("Failed to create subscription to '"+Global.topic_mappings["/motor_command"]+"'")
	else:
		print("Subscription created: ", motor_subscription)
	
	
	# Create Publishers
	key_states_publisher = create_publisher(
		"std_msgs/msg/String",
		Global.topic_mappings["/key_states"],
		10
	)
	if key_states_publisher == null:
		SignalBus.error.emit("Failed to create publisher to '"+Global.topic_mappings["/key_states"]+"'")
	else:
		print("Publisher created: ", key_states_publisher)
	
	servo_publisher = create_publisher( #TODO: This needs to actually go to /gound/joy - joy_to_servo
		"std_msgs/msg/String",
		Global.topic_mappings["/servo_command"],
		10
	)
	if servo_subscription == null:
		SignalBus.error.emit("Failed to create publisher to '"+Global.topic_mappings["/servo_command"]+"'")
	else:
		print("Publisher created: ", servo_subscription)
	
	SignalBus.outgoing_data.connect(_publish_data)
	SignalBus.publish_lights_data.connect(_publish_to_joy)



func _process(_delta: float) -> void:
	spin_some()
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
	# C - set control to camera
	# D - set control to dome lights
	# E - set control to exterior lights
	# UP - camera up
	# DOWN - camera down
	# LEFT - camera left
	# RIGHT - camera right
	# BACKSPACE - reset
	# X - reset camera x (used with BACKSPACE)
	# Y - reset camera y (used with BACKSPACE)

## Process data from ROS before sending to UI components
func _on_message_received(msg):
	var data: Dictionary[String,Variant] = {}
	var pieces_of_data = msg.data.split(",")
	for d in pieces_of_data:
		var data_parts = d.split("=")
		data[data_parts.get(0)] = data_parts.get(1)
	if data != {}:
		SignalBus.incoming_data.emit(data)

## Send camera image to display
func _handle_image(msg) -> void:
	SignalBus.incoming_video.emit(msg)

## Send datato ROS topics
func _publish_data(pub_name: String, data: Dictionary[String, Variant]):
	if pub_name == "servo":
		var output = []
		for key in data:
			output.append(key + ":" + str(data[key]))
		var msg = RosMsg.create("std_msgs/msg/String")
		msg.data = ",".join(output)
		servo_publisher.publish(msg)


## Publish data to ROS topic for turning lights on and off
func _publish_to_joy(button: String):
	var msg = RosMsg.create("sensor_msgs/msg/Joy")
	var buttons = []
	buttons.resize(11)
	buttons.fill(0)
	if button == "e":
		buttons.set(0, 1)
	elif button == "d":
		buttons.set(3, 1)
	
	msg.buttons = buttons
	
	joy_servo_publisher.publish(msg)
