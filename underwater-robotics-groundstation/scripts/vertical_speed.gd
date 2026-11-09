extends VSlider


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	SignalBus.incoming_data.connect(display_data)

func display_data(data: Dictionary[String, Variant]) -> void:
	var keys = ["vfr", "vfl", "vbr", "vbl"]
	var avg = 0.0
	var count = 0
	
	for key in keys:
		if data.has(key):
			#print("Adding: ", data[key])
			avg += float(data[key])
			count += 1
	if avg == 0:
		avg = 1500
	else:
		avg = avg / count
	#TODO: set display color
	value= avg
	
	
