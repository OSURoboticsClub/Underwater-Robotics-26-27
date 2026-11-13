extends VSlider


func _ready() -> void:
	SignalBus.incoming_data.connect(display_data)


func display_data(data: Dictionary[String, Variant]) -> void:
	var keys = ["vfr", "vfl", "vbr", "vbl"]
	var total = 0.0
	var count = 0

	for key in keys:
		if data.has(key):
			total += float(data[key])
			count += 1

	if count > 0:
		value = total / count
	else:
		value = 1500.0
