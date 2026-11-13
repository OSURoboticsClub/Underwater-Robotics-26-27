extends Control

@onready var inputs_container = $'Panel/Inputs'

# Called when the node enters the scene tree for the first time.
func _ready():
	# Get all actions defined in the Input Map
	var actions = InputMap.get_actions()
	
	for action in actions:
		if action.contains('ui_'):
			continue
		var hbox = HBoxContainer.new()
		hbox.name = action
		var label = Label.new()
		label.text = action.capitalize()
		var button = Button.new()
		button.text = InputMap.action_get_events(action)[0].as_text()
		button.pressed.connect(_remap.bind(action))
		#How do i set these properly
#		button.size_flags_horizontal.expand = true
#		button.size_flags_horizontal.
		hbox.add_child(label)
		hbox.add_child(button)
		inputs_container.add_child(hbox)

func _remap(action) -> void:
	pass

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(_delta: float) -> void:
	pass
