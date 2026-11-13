extends Node3D

## Animated crab that crawls along the seabed

var heading: float = 0.0
var walk_speed: float = 0.35
var anim_phase: float = 0.0
var change_timer: float = 0.0

@onready var left_claw = $Body/LeftClaw
@onready var right_claw = $Body/RightClaw


func _ready() -> void:
	heading = randf_range(0.0, TAU)
	rotation.y = heading


func _process(delta: float) -> void:
	anim_phase += delta * 4.0
	change_timer -= delta

	if change_timer <= 0.0:
		change_timer = randf_range(2.0, 6.0)
		heading += randf_range(-0.8, 0.8)
		rotation.y = heading

	# Crawl sideways (classic crab motion)
	var forward = -transform.basis.z
	global_position += forward * walk_speed * delta

	# Animate pincers
	if left_claw and right_claw:
		left_claw.rotation.y = sin(anim_phase) * 0.25
		right_claw.rotation.y = -sin(anim_phase) * 0.25
