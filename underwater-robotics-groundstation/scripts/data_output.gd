extends VBoxContainer

#@onready var lfl := $"ROVDisplay/Left/lfl"

func _ready() -> void:
	SignalBus.incoming_data.connect(process_data)

func process_data(data: Dictionary[String, Variant]) -> void:
	#print("-----Updating data-----")
	for key in data:
		#print("Key: " + key + " -> Value: " + data[key])
		var label: DataLabel = get_node_or_null(key)
		if label == null:
			SignalBus.error.emit("Failed to find label for: " + key)
		else:
			label.set_data(data[key])
			"""if key == "lfl":
				if int(data[key]) > 1500:
					lfl.add_theme_color_override("font_color", Color.RED)
				elif int(data[key]) < 1500:
					lfl.add_theme_color_override("font_color", Color.GREEN)
				else:
					lfl.add_theme_color_override("font_color", Color.WHITE)
			
		"""
