extends Node

## Default topic mappings
var topic_mappings : Dictionary[String, String] = {
	"/servo_command": "/servo_command",
	"/joy": "/joy",
	"/image_raw": "/image_raw",
	"/motor_command": "/motor_command",
	"/key_states": "/key_states",
} # Internal name: the actual ROS topic to look at


func _ready() -> void:
	# Read remappings from a file
	var remappings: PackedStringArray = load_from_file().split("\n",false)
	
	# Override with cmdline args
	var args = OS.get_cmdline_user_args()
	for a in args:
		remappings.append(a.trim_prefix("--"))
	for remapping in remappings:
		print(remapping)
		var parts = remapping.split(":")
		topic_mappings[parts[0].strip_edges()] = parts[1].strip_edges()


## Get data from the saved file
func load_from_file():
	var file = FileAccess.open("res://remaps.txt", FileAccess.READ) #TODO: Do a different file path
	if file:
		var content = file.get_as_text()
		return content
	else: 
		return ""


func _unhandled_key_input(event: InputEvent) -> void:
	if event.is_action_pressed("quit"):
		shut_down()
	# Display a error for testing error system
	elif event.is_action_pressed("error"):
		SignalBus.error.emit("This is a test error!")
	

## Close the running window
## @experimental: This doesn't yet tell ROS nodes to shutdown. Maybe in the future.
func shut_down() -> void:
	#TODO: send ros info to shutdown
	get_tree().quit()
