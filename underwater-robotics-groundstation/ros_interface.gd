extends RosNode

var subscription: RosSubscription
var key_states_publisher: RosPublisher
var joy_publisher: RosPublisher

var video_subscription: RosSubscription

#func _enter_tree() -> void:
#	ros_node_name = "godot_test"
#	pass

func _ready():
	ros_node_name = "godot_test" # Setting node name doesnt work.
	await get_tree().process_frame

	subscription = create_subscription(
		"std_msgs/msg/String",
		"/servo_command",
		_on_message_received,
		10
	)
	if subscription == null:
		SignalBus.error.emit("Failed to create subscription to '/servo_command'")
	else:
		print("Subscription created: ", subscription)
		
	
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
	
	key_states_publisher = create_publisher(
		"std_msgs/msg/String",
		"/key_states",
		10
	)
	if key_states_publisher == null:
		SignalBus.error.emit("Failed to create publisher to '/key_states'")
	else:
		print("Publisher created: ", key_states_publisher)
	
	
	joy_publisher = create_publisher(
		"sensor_msgs/msg/Joy",
		"/joy",
		10
	)
	if joy_publisher == null:
		SignalBus.error.emit("Failed to create publisher to '/joy'")
	else:
		print("Publisher created: ", joy_publisher)

	

func _physics_process(_delta):
	spin_some()
	
	if Input.is_key_pressed(KEY_P):
		SignalBus.error.emit("New Test Error")
	
	if Input.is_action_pressed("up"):
		print("Sending message")
		var msg = RosMsg.create("std_msgs/msg/String")
		msg.data = "UP"
		key_states_publisher.publish(msg)
	#list of keys the are used in other nodes:
	# C - camera
	# D
	# E
	# UP
	# DOWN
	# LEFT
	# RIGHT
	# BACKSPACE
	# X
	# Y
	
# This doesnt support holding down the key
"""func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("up"):
		print("Sending message")
		var msg = RosMsg.create("std_msgs/msg/String")
		msg.data = "UP"
		publisher.publish(msg)"""
		

func _on_message_received(msg):
	print("RECEIVED MESSAGE: ", msg.data)
	var data: Dictionary[String,Variant] = {
		"test": 1234
	}
	var pieces_of_data = msg.data.split(",")
	for d in pieces_of_data:
		var data_parts = d.split("=")
		#print("data_parts: " + str(data_parts))
		data[data_parts[0]] = data_parts.get(1) #TODO: this is a PAcked string array
	if data != {}:
		SignalBus.incoming_data.emit(data)


func _handle_image(msg) -> void:
	#var texture = create_camera_texture(msg)
	#SignalBus.incoming_video.emit(create_camera_texture(msg))
	SignalBus.incoming_video.emit(msg)

func convert_ros_image(msg) -> Image:
	var width: int = msg.width
	var height: int = msg.height
	var encoding: String = msg.encoding
	var data: PackedByteArray = msg.data

	if width <= 0 or height <= 0:
		push_warning("Invalid camera image dimensions")
		return null

	if encoding != "rgb8" and encoding != "bgr8":
		push_warning("Unsupported image encoding: " + encoding)
		return null

	var expected_size: int = width * height * 3

	if data.size() < expected_size:
		push_warning("Camera image data is smaller than expected")
		return null

	if encoding == "bgr8":
		data = data.duplicate()

		for i in range(0, expected_size, 3):
			var temp: int = data[i]
			data[i] = data[i + 2]
			data[i + 2] = temp

	var image := Image.create_from_data(
		width,
		height,
		false,
		Image.FORMAT_RGB8,
		data
	)

	return image

func create_camera_texture(msg) -> ImageTexture:
	var image: Image = convert_ros_image(msg)

	if image == null:
		SignalBus.error.emit("After converting from ros to image: its null")
		return null

	var texture := ImageTexture.create_from_image(image)

	return texture


#Ideas
# Global Signalbus
# - sends out a signal with name and value
# - example camera_x, 1440
# Scenes can subscribe and then process the name to see
# if they use it.

# Or, each one has its own signal that gets sent, but
# that might be too much
