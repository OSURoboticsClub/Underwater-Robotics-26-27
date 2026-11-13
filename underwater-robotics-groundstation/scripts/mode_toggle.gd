extends Button

@onready var camera_feed = $"../../Camera Feed"


func _ready() -> void:
	pressed.connect(_on_pressed)
	_update_text()


func _on_pressed() -> void:
	if camera_feed:
		camera_feed.set_sim_mode(!camera_feed.use_sim_mode)
		_update_text()


func _update_text() -> void:
	if camera_feed and camera_feed.use_sim_mode:
		text = "3D Simulator Mode [ON]"
	else:
		text = "Live ROS 2 Mode [ON]"
