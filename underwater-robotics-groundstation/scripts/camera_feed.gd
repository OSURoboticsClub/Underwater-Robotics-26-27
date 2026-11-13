extends TextureRect

var camera_texture: ImageTexture

var thread: Thread
var mutex: Mutex
var semaphore: Semaphore
var is_running := true

# Latest incoming frame waiting for processing
var pending_frame: Dictionary = {}
var has_new_frame := false

# Latest processed image waiting for the main thread
var ready_image: Image = null
var has_ready_image := false

# 3D Godot Simulation mode toggle
@export var use_sim_mode: bool = true
var sim_viewport: SubViewport = null


func _ready() -> void:
	mutex = Mutex.new()
	semaphore = Semaphore.new()
	thread = Thread.new()

	sim_viewport = get_node_or_null("../SimViewport")
	if sim_viewport and use_sim_mode:
		texture = sim_viewport.get_texture()

	SignalBus.incoming_video.connect(on_incoming_video_signal)
	thread.start(_thread_loop)


func set_sim_mode(enabled: bool) -> void:
	use_sim_mode = enabled
	if use_sim_mode:
		if sim_viewport:
			texture = sim_viewport.get_texture()
	else:
		if camera_texture:
			texture = camera_texture


func on_incoming_video_signal(image_msg) -> void:
	if use_sim_mode:
		return

	if image_msg == null:
		SignalBus.error.emit("An image was not supplied")
		return

	if image_msg.encoding != "rgb8":
		return

	# Copy the required fields while the ROS message is available
	var frame: Dictionary = {
		"width": image_msg.width,
		"height": image_msg.height,
		"data": image_msg.data.duplicate(),
	}

	mutex.lock()
	pending_frame = frame
	has_new_frame = true
	mutex.unlock()

	semaphore.post()


func _process(_delta: float) -> void:
	if use_sim_mode:
		if sim_viewport and texture != sim_viewport.get_texture():
			texture = sim_viewport.get_texture()
		return

	var image_to_display: Image = null

	mutex.lock()
	if has_ready_image:
		image_to_display = ready_image
		ready_image = null
		has_ready_image = false
	mutex.unlock()

	if image_to_display != null:
		_update_display_texture(image_to_display)


func _thread_loop() -> void:
	while true:
		semaphore.wait()

		var current_frame: Dictionary = {}

		mutex.lock()
		if not is_running:
			mutex.unlock()
			break

		if has_new_frame:
			current_frame = pending_frame
			pending_frame = {}
			has_new_frame = false
		mutex.unlock()

		if current_frame.is_empty():
			continue

		var local_image := Image.create_from_data(
			current_frame["width"],
			current_frame["height"],
			false,
			Image.FORMAT_RGB8,
			current_frame["data"]
		)

		mutex.lock()
		ready_image = local_image
		has_ready_image = true
		mutex.unlock()


func _update_display_texture(new_image: Image) -> void:
	if camera_texture == null:
		camera_texture = ImageTexture.create_from_image(new_image)
		texture = camera_texture
	else:
		camera_texture.update(new_image)


func _exit_tree() -> void:
	mutex.lock()
	is_running = false
	mutex.unlock()

	semaphore.post()

	if thread and thread.is_started():
		thread.wait_to_finish()

	if SignalBus.incoming_video.is_connected(on_incoming_video_signal):
		SignalBus.incoming_video.disconnect(on_incoming_video_signal)
