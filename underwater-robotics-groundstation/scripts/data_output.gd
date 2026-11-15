extends VBoxContainer


func _ready() -> void:
	SignalBus.incoming_data.connect(process_data)

func process_data(data: Dictionary[String, Variant]) -> void:
	for key in data:
		var label: DataLabel = get_node_or_null(key)
		if label == null:
			SignalBus.error.emit("Failed to find label for: " + key)
		else:
			label.set_data(data[key])
			
			# Color code ROV motor displays
			for motor_display in $"ROVDisplay/Left".get_children() + $"ROVDisplay/Right".get_children():
				if motor_display.name == key:
					if int(data[key]) < 1500:
						motor_display.label_settings.font_color = Color.RED
					elif int(data[key]) > 1500:
						motor_display.label_settings.font_color = Color.GREEN
					else:
						motor_display.label_settings.font_color = Color.WHITE
					
			
		
