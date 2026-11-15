@tool
class_name DataLabel
extends Label

## A label specificlly for displaying data from a ROS2 node.

## The text that labels the proceeding data.
@export var prefix: String = 'Data':
	set(value):
		prefix = value
		_update_editor_text()

## The name of the data as it comes from the ROS2 node.
@export var data_name: String = 'example_data':
	set(value):
		data_name = value
		_update_editor_text()

## Default data value to display before
## any real data has been recieved.
@export var start_value: String = '1500':
	set(value):
		start_value = value
		_update_editor_text()

func _ready() -> void:
	set_data(start_value)
	# Sets the node's name so that it can easily be found later
	if not Engine.is_editor_hint():
		if data_name:
			name = data_name
		else:
			SignalBus.error.emit("DataLabel(" + name + ") wasnt given name of data")

## Update the labels text using the data passed in,
## and the assigned prefix.
func set_data(data: String) -> void:
	text = prefix + ": " + data

## Update the labels text while in the editor, using the
## start_value.
func _update_editor_text():
	# Sets the starting text
	if start_value:
		set_data(start_value)
	else:
		set_data("0.0")
