extends VBoxContainer

@onready var top = $"ProgressBarTop"
@onready var bottom = $"ProgressBarBottom"

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	SignalBus.incoming_data.connect(display_data)

func display_data(data: Dictionary[String, Variant]) -> void:
	var keys = ["vfr", "vfl", "vbr", "vbl"]
	var avg = 0.0
	var count = 0
	
	for key in keys:
		if data.has(key):
			avg += float(data[key])
			count += 1
	if avg == 0:
		avg = 1500
	else:
		avg = avg / count
	
	# Apply this value to the progress bars
	if avg == 1500:
		top.value = 0
		bottom.value = 0
	elif avg > 1500:
		top.value = avg
		bottom.value = 0
	elif avg < 1500:
		top.value = 0
		bottom.value = 1500 - avg
