extends VBoxContainer

const INPUT_BINDINGS_PATH := "user://input_bindings.cfg"
const REMAPPABLE_ACTIONS: Array[StringName] = [
	&"up",
	&"down",
	&"left",
	&"right",
	&"dome_lights",
	&"exterior_lights",
	&"camera",
	&"reset",
	&"x",
	&"y",
	&"fullscreen",
]

@onready var vbox: VBoxContainer = $ActionScroll/ActionList
@onready var profile_name_input: LineEdit = $ProfileControls/SaveRow/ProfileNameInput
@onready var saved_profiles: OptionButton = $ProfileControls/LoadRow/SavedProfiles
@onready var status_label: Label = $StatusLabel

var current_remap: StringName = &""
var remap_buttons: Dictionary[StringName, Button] = {}


func _ready() -> void:
	#TODO: save default controls as "Default", and when you try and change default
	# it just creates a new setup.
	profile_name_input.text = "Default"
	_on_save_profile_pressed()
	profile_name_input.text = ""
	# How do you make it so that you cant edit the saved defaults.
	_build_controls()
	$ProfileControls/SaveRow/SaveButton.pressed.connect(_on_save_profile_pressed)
	$ProfileControls/LoadRow/LoadButton.pressed.connect(_on_load_profile_pressed)
	$ResetButton.pressed.connect(_on_reset_button_pressed)
	visibility_changed.connect(_on_visibility_changed)
	_refresh_saved_profiles()


func _build_controls() -> void:
	vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	for action: StringName in REMAPPABLE_ACTIONS:
		if not InputMap.has_action(action):
			push_warning("Cannot add a control for missing input action: %s" % action)
			continue

		var hbox := HBoxContainer.new()
		var label := Label.new()
		var button := Button.new()
		hbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		label.text = snake_case_to_normal(String(action))
		button.custom_minimum_size.x = 140.0
		button.text = get_action_key_name(action)
		button.pressed.connect(_begin_remap.bind(action, button))
		hbox.add_child(label)
		hbox.add_child(button)
		vbox.add_child(hbox)
		remap_buttons[action] = button


func _on_close_button_pressed() -> void:
	_cancel_remap()
	visible = false


func snake_case_to_normal(text: String, capitalize_words: bool = true) -> String:
	var words := text.split("_")
	if capitalize_words:
		for i in range(words.size()):
			words[i] = words[i].capitalize()
	return " ".join(words)


func get_action_key_name(action_name: StringName) -> String:
	if not InputMap.has_action(action_name):
		return "No Key Assigned"

	for event in InputMap.action_get_events(action_name):
		if event is InputEventKey:
			return event.as_text()
	return "No Key Assigned"


func _begin_remap(action: StringName, button: Button) -> void:
	_cancel_remap()
	current_remap = action
	button.text = "Press a key..."
	button.grab_focus()
	_show_status("Press a key for %s. Escape cancels." % snake_case_to_normal(String(action)))


func _input(event: InputEvent) -> void:
	if current_remap == &"" or not event is InputEventKey:
		return

	get_viewport().set_input_as_handled()
	var key_event := event as InputEventKey
	if not key_event.pressed or key_event.echo:
		return

	if key_event.keycode == KEY_ESCAPE:
		_cancel_remap()
		_show_status("Remapping cancelled.")
		return

	var action_to_remap := current_remap
	current_remap = &""
	remap_action_to_key(action_to_remap, key_event)


func _cancel_remap() -> void:
	if remap_buttons.has(current_remap):
		remap_buttons[current_remap].text = get_action_key_name(current_remap)
	current_remap = &""


func _on_visibility_changed() -> void:
	if not is_visible_in_tree():
		_cancel_remap()


func remap_action_to_key(action_name: StringName, key_event: InputEventKey) -> void:
	if not InputMap.has_action(action_name):
		push_error("Cannot remap missing input action: %s" % action_name)
		current_remap = &""
		return

	var new_event := InputEventKey.new()
	new_event.physical_keycode = (
		key_event.physical_keycode if key_event.physical_keycode != 0 else key_event.keycode
	)
	new_event.keycode = key_event.keycode
	new_event.shift_pressed = key_event.shift_pressed
	new_event.alt_pressed = key_event.alt_pressed
	new_event.ctrl_pressed = key_event.ctrl_pressed
	new_event.meta_pressed = key_event.meta_pressed

	for existing_event in InputMap.action_get_events(action_name):
		if existing_event is InputEventKey:
			InputMap.action_erase_event(action_name, existing_event)
	InputMap.action_add_event(action_name, new_event)

	if remap_buttons.has(action_name):
		remap_buttons[action_name].text = new_event.as_text()
	current_remap = &""
	_show_status(
		"%s is now bound to %s."
		% [snake_case_to_normal(String(action_name)), new_event.as_text()]
	)


func _on_save_profile_pressed() -> void:
	_cancel_remap()
	var profile_name := profile_name_input.text.strip_edges()
	if profile_name.is_empty():
		_show_status("Enter a name for this mapping.")
		return

	var bindings: Dictionary = {}
	for action: StringName in REMAPPABLE_ACTIONS:
		if not InputMap.has_action(action):
			continue
		bindings[String(action)] = {}
		for event in InputMap.action_get_events(action):
			if event is InputEventKey:
				bindings[String(action)] = _key_event_to_dictionary(event)
				break

	var config := ConfigFile.new()
	var load_error := config.load(INPUT_BINDINGS_PATH)
	if load_error != OK and load_error != ERR_FILE_NOT_FOUND:
		push_error("Failed to read saved input mappings: %s" % load_error)
		_show_status("Could not read saved mappings.")
		return

	config.set_value("profiles", profile_name, bindings)
	var save_error := config.save(INPUT_BINDINGS_PATH)
	if save_error != OK:
		push_error("Failed to save input mapping (%s): %s" % [INPUT_BINDINGS_PATH, save_error])
		_show_status("Could not save mapping.")
		return

	_refresh_saved_profiles(profile_name)
	_show_status("Saved mapping: %s" % profile_name)


func _on_load_profile_pressed() -> void:
	_cancel_remap()
	if saved_profiles.item_count == 0 or saved_profiles.selected < 0:
		_show_status("Select a saved mapping to load.")
		return

	var profile_name := String(saved_profiles.get_item_metadata(saved_profiles.selected))
	var config := ConfigFile.new()
	var load_error := config.load(INPUT_BINDINGS_PATH)
	if load_error != OK:
		push_error("Failed to load saved input mappings (%s): %s" % [INPUT_BINDINGS_PATH, load_error])
		_show_status("Could not load saved mappings.")
		return

	var profile: Variant = config.get_value("profiles", profile_name, null)
	if not profile is Dictionary:
		push_error("Saved input mapping is missing or invalid: %s" % profile_name)
		_show_status("Selected mapping is invalid.")
		return

	for action: StringName in REMAPPABLE_ACTIONS:
		var action_name := String(action)
		if not InputMap.has_action(action) or not profile.has(action_name):
			continue

		var saved_binding: Variant = profile[action_name]
		if not saved_binding is Dictionary:
			push_warning("Ignoring invalid saved binding for action: %s" % action)
			continue
		var key_event := _dictionary_to_key_event(saved_binding)
		if not saved_binding.is_empty() and key_event == null:
			push_warning("Ignoring invalid key binding for action: %s" % action)
			continue

		_clear_keyboard_bindings(action)
		if key_event == null:
			continue
		InputMap.action_add_event(action, key_event)

	_refresh_mapping_button_texts()
	_show_status("Loaded mapping: %s" % profile_name)


func _refresh_saved_profiles(select_name: String = "") -> void:
	saved_profiles.clear()
	var config := ConfigFile.new()
	var load_error := config.load(INPUT_BINDINGS_PATH)
	if load_error == ERR_FILE_NOT_FOUND:
		return
	if load_error != OK:
		push_error("Failed to read saved input mappings (%s): %s" % [INPUT_BINDINGS_PATH, load_error])
		_show_status("Could not read saved mappings.")
		return
	if not config.has_section("profiles"):
		return

	var profile_names := config.get_section_keys("profiles")
	profile_names.sort()
	for profile_name: String in profile_names:
		var index := saved_profiles.item_count
		saved_profiles.add_item(profile_name)
		saved_profiles.set_item_metadata(index, profile_name)
		if profile_name == select_name:
			saved_profiles.select(index)


func _key_event_to_dictionary(key_event: InputEventKey) -> Dictionary:
	return {
		"physical_keycode": int(key_event.physical_keycode),
		"keycode": int(key_event.keycode),
		"shift_pressed": key_event.shift_pressed,
		"alt_pressed": key_event.alt_pressed,
		"ctrl_pressed": key_event.ctrl_pressed,
		"meta_pressed": key_event.meta_pressed,
	}


func _dictionary_to_key_event(saved_binding: Dictionary) -> InputEventKey:
	var key_event := InputEventKey.new()
	key_event.physical_keycode = int(saved_binding.get("physical_keycode", 0)) as Key
	key_event.keycode = int(saved_binding.get("keycode", 0)) as Key
	key_event.shift_pressed = bool(saved_binding.get("shift_pressed", false))
	key_event.alt_pressed = bool(saved_binding.get("alt_pressed", false))
	key_event.ctrl_pressed = bool(saved_binding.get("ctrl_pressed", false))
	key_event.meta_pressed = bool(saved_binding.get("meta_pressed", false))
	if key_event.physical_keycode == 0 and key_event.keycode == 0:
		return null
	return key_event


func _clear_keyboard_bindings(action_name: StringName) -> void:
	for existing_event in InputMap.action_get_events(action_name):
		if existing_event is InputEventKey:
			InputMap.action_erase_event(action_name, existing_event)


func _on_reset_button_pressed() -> void:
	_cancel_remap()
	InputMap.load_from_project_settings()
	_refresh_mapping_button_texts()
	_show_status("Restored project default keybinds.")


func _refresh_mapping_button_texts() -> void:
	for action: StringName in remap_buttons:
		remap_buttons[action].text = get_action_key_name(action)


func _show_status(message: String) -> void:
	status_label.text = message
