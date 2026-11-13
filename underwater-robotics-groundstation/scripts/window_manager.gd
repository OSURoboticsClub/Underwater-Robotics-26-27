extends Node

#@onready var cameras_window: Window = $'CamerasWindow'
# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	pass
	#if cameras_window:
		#cameras_window.close_requested.connect(func(): cameras_window.queue_free())

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("fullscreen"):
		if get_window().mode == Window.MODE_FULLSCREEN:
			get_window().mode = Window.MODE_MAXIMIZED
		else:
			get_window().mode = Window.MODE_FULLSCREEN
