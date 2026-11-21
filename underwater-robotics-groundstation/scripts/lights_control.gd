extends VBoxContainer

## Button to toggle exterior lights
@onready var exterior_button := $"ExteriorLights/EnabledButton"
## Slider to control exterior lights brightness
@onready var exterior_slider := $"ExteriorLights/HBoxContainer/HSlider"
## Button to toggle dome lights
@onready var dome_button := $"DomeLights/EnabledButton"
## Slider to control dome lights brightness
@onready var dome_slider := $"DomeLights/HBoxContainer/HSlider"


func _ready() -> void:
	# Connect signals
	SignalBus.incoming_data.connect(process_data)
	exterior_button.pressed.connect(toggle_exterior)
	dome_button.pressed.connect(toggle_dome)
	
	exterior_slider.drag_ended.connect(update_brightness)
	dome_slider.drag_ended.connect(update_brightness)


## Publish data to ROS to turn on exterior lights
func toggle_exterior():
	SignalBus.publish_lights_data.emit("e")

## Publish data to ROS to turn on dome lights
func toggle_dome():
	SignalBus.publish_lights_data.emit("d")

## Publish light brightness to ROS
## @experimental: Data isn't able to be recieved by ROS in this format. 
func update_brightness(changed: bool):
	if !changed: # Return if the value wasn't acctually changed
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
