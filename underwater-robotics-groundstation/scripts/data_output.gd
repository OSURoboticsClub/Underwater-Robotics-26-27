extends VBoxContainer


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	SignalBus.incoming_data.connect(process_data)


func process_data(data: Dictionary[String, Variant]) -> void:
	"""#try out this
	for key, value in user_profile.items():
		print(f"Key: {key} -> Value: {value}")
	"""
	if data.get("camera_x") != null:
		print("updating data")
		var label = get_node("camera_x")
		label.text = "Camera X: " + str(data["camera_x"])
		#can i dynamically see what data was given and then for each of those 
		# get its label and update it
	else:
		print("no good data")
