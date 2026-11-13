extends VBoxContainer

@onready var exterior_button := $"ExteriorLights/EnabledButton"
@onready var exterior_slider := $"ExteriorLights/HBoxContainer/HSlider"
@onready var dome_button := $"DomeLights/EnabledButton"
@onready var dome_slider := $"DomeLights/HBoxContainer/HSlider"


func _ready() -> void:
	SignalBus.incoming_data.connect(process_data)
	exterior_button.pressed.connect(toggle_exterior)
	dome_button.pressed.connect(toggle_dome)

	exterior_slider.drag_ended.connect(update_brightness)
	dome_slider.drag_ended.connect(update_brightness)


func toggle_exterior() -> void:
	var output: Dictionary[String, Variant] = {
		"ext_lights": int(exterior_button.button_pressed)
	}
	SignalBus.outgoing_data.emit("servo", output)


func toggle_dome() -> void:
	var output: Dictionary[String, Variant] = {
		"dome_lights": int(dome_button.button_pressed)
	}
	SignalBus.outgoing_data.emit("servo", output)


func update_brightness(changed: bool) -> void:
	if not changed:
		return
	var output: Dictionary[String, Variant] = {
		"ext_lights_max": float(exterior_slider.value),
		"dome_lights_max": float(dome_slider.value)
	}
	SignalBus.outgoing_data.emit("servo", output)


func process_data(data: Dictionary[String, Variant]) -> void:
	if data.has("ext_lights"):
		exterior_button.button_pressed = bool(int(data["ext_lights"]))
	if data.has("ext_lights_max"):
		exterior_slider.value = float(data["ext_lights_max"])

	if data.has("dome_lights"):
		dome_button.button_pressed = bool(int(data["dome_lights"]))
	if data.has("dome_lights_max"):
		dome_slider.value = float(data["dome_lights_max"])
