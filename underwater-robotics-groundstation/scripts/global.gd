extends Node

func _unhandled_key_input(event: InputEvent) -> void:
	if event.is_action_pressed("error"):
		SignalBus.error.emit("This is a test error!")
	
	elif event.is_action_pressed("quit"):
		shut_down()
	

func shut_down() -> void:
	#TODO: send ros info to shutdown
	get_tree().quit()
