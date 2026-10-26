extends Node

@onready var cameras_window: Window = $'Window'
# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	cameras_window.close_requested.connect(func(): cameras_window.queue_free())


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass


func shut_down() -> void:
	#TODO: send ros info to shutdown
	get_tree().quit()