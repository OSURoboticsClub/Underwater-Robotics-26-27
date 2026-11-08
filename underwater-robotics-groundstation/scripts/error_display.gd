class_name ErrorDisplay
extends VBoxContainer
## Displays errors that are sent out by the signal.

## The display color for an outputted error.
@export var error_color: Color = Color.RED

## The max number of errors to display
@export var max_errors: int = 40

func _ready() -> void:
	SignalBus.error.connect(_add_error)

## Adds an error label to the screen
func _add_error(e:String) -> void:
	push_error(e)
	var label = Label.new()
	label.name = 'Error'
	label.text = e
	label.add_theme_color_override("font_color", error_color)
	add_child(label)
	_scroll_to_bottom()
	_limit_size()

## Scroll to the bottom of the list to show newest errors.
func _scroll_to_bottom():
	await get_tree().process_frame
	
	var scrollbar = get_parent().get_v_scroll_bar()
	get_parent().scroll_vertical = scrollbar.max_value

## Remove old error Labels.
func _limit_size() -> void:
	while get_child_count() > max_errors:
		get_children()[0].queue_free()
