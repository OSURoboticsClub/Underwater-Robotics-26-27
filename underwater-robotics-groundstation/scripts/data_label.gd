class_name DataLabel
extends Label

## A label specificlly for displaying data from a ROS2 node.

## The text that labels the proceeding data.
@export var prefix: String = 'Data'

## The name of the data as it comes from the ROS2 node.
@export var data_name: String = 'data'

## Default data value to display before
## any real data has been recieved.
@export var start_value: String = '1500'

func _ready() -> void:
	# Sets the node's name so that it can easily be found later
	if not Engine.is_editor_hint():
		if data_name:
			name = data_name
		else:
			SignalBus.error.emit("DataLabel(" + name + ") wasnt given name of data")
		
		set_data(start_value)
	
## Update the labels text using the data passed in,
## and the assigned prefix.
func set_data(data: String) -> void:
	text = prefix + ": " + data
