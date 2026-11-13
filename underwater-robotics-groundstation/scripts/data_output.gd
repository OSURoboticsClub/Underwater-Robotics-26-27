extends VBoxContainer


func _ready() -> void:
	SignalBus.incoming_data.connect(process_data)


func process_data(data: Dictionary[String, Variant]) -> void:
	for key in data:
		var label: DataLabel = get_node_or_null(key)
		if label != null:
			label.set_data(str(data[key]))
