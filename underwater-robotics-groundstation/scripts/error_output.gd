extends VBoxContainer
# Displays errors that are sent out by the signal

@export var error_color := Color.RED

func _ready() -> void:
	SignalBus.error.connect(_add_error)

# Adds an error label to the screen
func _add_error(e:String) -> void:
	push_error(e)
	var label = Label.new()
	label.name = 'Error'
	label.text = e
	label.add_theme_color_override("font_color", Color.RED)
	add_child(label)
	scroll_to_bottom()

# Scroll to the bottom of the list to see newest error
func scroll_to_bottom():
	await get_tree().process_frame
	
	var scrollbar = get_parent().get_v_scroll_bar()
	get_parent().scroll_vertical = scrollbar.max_value
