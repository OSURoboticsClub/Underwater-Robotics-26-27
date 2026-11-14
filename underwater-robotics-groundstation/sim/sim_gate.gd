class_name SimGate
extends Node3D

## Navigational Inspection Gate with Checkpoint Trigger & Visual Beacon

@export var gate_id: int = 1
@export var gate_name: String = "Gate 1"

var is_cleared: bool = false

@onready var beacon_light: OmniLight3D = $BeaconLight
@onready var trigger_area: Area3D = $TriggerArea
@onready var mesh_frame: MeshInstance3D = get_node_or_null("FrameMesh")

signal gate_passed(gate_id: int, gate_name: String)


func _ready() -> void:
	if trigger_area:
		trigger_area.body_entered.connect(_on_body_entered)
	reset_gate()


func _on_body_entered(body: Node3D) -> void:
	if is_cleared:
		return

	# Trigger on ROV
	if body is SimROV or body.name == "ROV":
		is_cleared = true
		if beacon_light:
			beacon_light.light_color = Color(0.1, 1.0, 0.35, 1.0) # Vibrant green
			beacon_light.light_energy = 4.0
			beacon_light.omni_range = 12.0
		gate_passed.emit(gate_id, gate_name)


func reset_gate() -> void:
	is_cleared = false
	if beacon_light:
		beacon_light.light_color = Color(1.0, 0.65, 0.1, 1.0) # Amber awaiting
		beacon_light.light_energy = 2.5
		beacon_light.omni_range = 8.0
