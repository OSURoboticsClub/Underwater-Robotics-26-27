extends VBoxContainer

@onready var exterior_button := $"ExteriorLights/EnabledButton"
@onready var exterior_slider := $"ExteriorLights/HBoxContainer/HSlider"
@onready var dome_button := $"DomeLights/EnabledButton"
@onready var dome_slider := $"DomeLights/HBoxContainer/HSlider"

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	SignalBus.incoming_data.connect(process_data)
	exterior_button.pressed.connect(toggle_exterior)
	dome_button.pressed.connect(toggle_dome)
	#TODO: connect dome light button
	
	exterior_slider.drag_ended.connect(update_brightness)
	dome_slider.drag_ended.connect(update_brightness)
	

# this is only triggered by a mouse click, not toggling in code.
func toggle_exterior():
	#var output : Dictionary[String, Variant] = {}
	#output["ext_lights"] = int(exterior_button.button_pressed)
	#SignalBus.outgoing_data.emit("servo", output)
	SignalBus.publish_lights_data.emit("e")
	pass
	
func toggle_dome():
	SignalBus.publish_lights_data.emit("d")
	pass

func update_brightness(changed: bool):
	if !changed: # The value wasnt acctually changed
		return
	var output : Dictionary[String, Variant] = {}
	output["ext_lights_max"] = float(exterior_slider.value)
	output["dome_lights_max"] = float(dome_slider.value)
	#SignalBus.outgoing_data.emit("servo", output) #TODO: emit signal, and send to right publisher

func process_data(data: Dictionary[String, Variant]):
	# Process data for exterior lights
	if data.has("ext_lights"):
		exterior_button.button_pressed = int(data["ext_lights"])
	if data.has("ext_lights_max"):
		exterior_slider.value = float(data["ext_lights_max"])
		
	# Process data for dome lights
	if data.has("dome_lights"):
		dome_button.button_pressed = int(data["dome_lights"])
	if data.has("dome_lights_max"):
		dome_slider.value = float(data["dome_lights_max"])
	pass
