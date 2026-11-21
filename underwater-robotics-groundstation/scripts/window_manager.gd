extends Node

func _unhandled_input(event: InputEvent) -> void:
	# Toggle Fullscreen
	if event.is_action_pressed("fullscreen"):
		if get_window().mode == Window.MODE_FULLSCREEN:
			get_window().mode = Window.MODE_MAXIMIZED
		else:
			get_window().mode = Window.MODE_FULLSCREEN
