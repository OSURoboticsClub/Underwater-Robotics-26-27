extends Node3D

## Animated swimming fish

var speed: float = 1.2
var phase: float = 0.0
var base_y: float = -5.0

@onready var tail = $Body/Tail


func _ready() -> void:
	speed = randf_range(0.9, 1.8)
	phase = randf_range(0.0, TAU)
	base_y = position.y


func _process(delta: float) -> void:
	phase += delta * speed * 3.5

	# Move forward along -Z
	position -= transform.basis.z * speed * delta

	# Gentle sine wave swimming motion
	position.y = base_y + sin(phase * 0.5) * 0.3

	# Wag tail
	if tail:
		tail.rotation.y = sin(phase) * 0.45

	# Wrap around boundary
	if position.z < -40.0:
		position.z = 25.0
		position.x = randf_range(-15.0, 15.0)
