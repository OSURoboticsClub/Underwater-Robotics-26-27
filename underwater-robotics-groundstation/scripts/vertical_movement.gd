extends VBoxContainer

## Progress bar for positive vertical movement
@onready var top: ProgressBar = $"ProgressBarTop"

## Progress bar for negative vertical movement
@onready var bottom: ProgressBar = $"ProgressBarBottom"

func _ready() -> void:
	SignalBus.incoming_data.connect(display_data)

## Filter out and display data related to vertical movement
func display_data(data: Dictionary[String, Variant]) -> void:
	## Pieces of data to look for
	var keys: Array[String] = ["vfr", "vfl", "vbr", "vbl"]
	## Average vertical speed
	var avg: float = 0.0
	var count: int = 0
	
	# Calculate average
	for key in keys:
		if data.has(key):
			avg += float(data[key])
			count += 1
	if avg == 0:
		avg = 1500
	else:
		avg = avg / count
	
	# Apply this value to the progress bars
	if avg == 1500: # Not moving
		top.value = 0
		bottom.value = 0
	elif avg > 1500: # Moving up
		top.value = avg
		bottom.value = 0
	elif avg < 1500: # Moveing down
		top.value = 0
		bottom.value = 1500 - avg
