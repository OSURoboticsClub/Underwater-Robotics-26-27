extends Node

# Internal name: the actual ROS topic to look at
var topic_mappings : Dictionary[String, String] = {
	"/servo_command": "/servo_command",
	"/joy": "/joy",
	"/image_raw": "/image_raw",
	"/motor_command": "/motor_command",
	"/key_states": "/key_states",
}


func _ready() -> void:
	# Read remappings from a file
	var remappings = load_from_file().split("\n",false)
	for remapping in remappings:
		var parts = remapping.split(":")
		topic_mappings[parts[0].strip_edges()] = parts[1].strip_edges()

func load_from_file():
	var file = FileAccess.open("res://remaps.txt", FileAccess.READ) # Do a different file path
	if file:
		var content = file.get_as_text()
		return content
	else: 
		return ""




func _unhandled_key_input(event: InputEvent) -> void:
	if event.is_action_pressed("error"):
		SignalBus.error.emit("This is a test error!")
	
	elif event.is_action_pressed("quit"):
		shut_down()
	

func shut_down() -> void:
	#TODO: send ros info to shutdown
	get_tree().quit()
