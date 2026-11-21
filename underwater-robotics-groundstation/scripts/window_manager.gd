extends Node

@onready var cameras_window: Window = $'Window'


func _ready() -> void:
	if is_instance_valid(cameras_window):
		cameras_window.close_requested.connect(func(): cameras_window.queue_free())
	get_tree().root.close_requested.connect(shut_down)


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		shut_down()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("close"):
		shut_down()
	elif event.is_action_pressed("fullscreen"):
		if get_window().mode == Window.MODE_FULLSCREEN:
			get_window().mode = Window.MODE_MAXIMIZED
		else:
			get_window().mode = Window.MODE_FULLSCREEN


func shut_down() -> void:
	if is_instance_valid(cameras_window):
		cameras_window.queue_free()
	get_tree().quit()
