extends RosNode

var subscription: RosSubscription
var key_states_publisher: RosPublisher
var joy_publisher: RosPublisher

var video_subscription: RosSubscription

var last_physics_time_usec: int = 0

#func _enter_tree() -> void:
#	ros_node_name = "godot_test"
#	pass

func _ready():
	ros_node_name = "groundstation" # Setting node name doesnt work.
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

	
func _process(_delta: float) -> void:
	var now := Time.get_ticks_usec()

	if last_physics_time_usec != 0:
		var interval_ms := (
			now - last_physics_time_usec
		) / 1000.0

		if interval_ms > 30.0:
			print("Physics interval: ", interval_ms, " ms")

	last_physics_time_usec = now

	var spin_start_usec := Time.get_ticks_usec()
	spin_some()
	var spin_duration_ms := (
		Time.get_ticks_usec() - spin_start_usec
	) / 1000.0

	if spin_duration_ms > 5.0:
		print("spin_some duration: ", spin_duration_ms, " ms")

	if Input.is_key_pressed(KEY_P):
		SignalBus.error.emit("New Test Error")

	if Input.is_action_pressed("up"):
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
	var data: Dictionary[String,Variant] = {}
	var pieces_of_data = msg.data.split(",")
	for d in pieces_of_data:
		var data_parts = d.split("=")
		#print("data_parts: " + str(data_parts))
		data[data_parts[0]] = data_parts.get(1) #TODO: this is a PAcked string array
	if data != {}:
		SignalBus.incoming_data.emit(data)


func _handle_image(msg) -> void:
	SignalBus.incoming_video.emit(msg)
