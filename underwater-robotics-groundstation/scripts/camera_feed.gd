extends TextureRect

var camera_texture: ImageTexture

var thread: Thread
var mutex: Mutex
var semaphore: Semaphore
var is_running := true

# Latest incoming frame waiting for processing.
var pending_frame: Dictionary = {}
var has_new_frame := false

# Latest processed image waiting for the main thread.
var ready_image: Image = null
var has_ready_image := false
var ready_image_time_usec: int = 0

# Timing measurements.
var last_callback_time_usec: int = 0
var last_display_time_usec: int = 0


func _ready() -> void:
	mutex = Mutex.new()
	semaphore = Semaphore.new()
	thread = Thread.new()

	SignalBus.incoming_video.connect(on_incoming_video_signal)
	thread.start(_thread_loop)


func on_incoming_video_signal(image_msg) -> void:
	var now := Time.get_ticks_usec()

	if last_callback_time_usec != 0:
		var interval_ms := (
			now - last_callback_time_usec
		) / 1000.0

		if interval_ms > 100.0:
			print("ROS callback interval: ", interval_ms, " ms")

	last_callback_time_usec = now

	if image_msg == null:
		SignalBus.error.emit("An image was not supplied")
		return

	if image_msg.encoding != "rgb8":
		return

	# Copy the required fields while the ROS message is available.
	var frame: Dictionary = {
		"width": image_msg.width,
		"height": image_msg.height,
		"data": image_msg.data.duplicate(),
		"received_time_usec": now
	}

	mutex.lock()
	pending_frame = frame
	has_new_frame = true
	mutex.unlock()

	semaphore.post()


func _process(_delta: float) -> void:
	var image_to_display: Image = null
	var image_ready_time: int = 0

	mutex.lock()

	if has_ready_image:
		image_to_display = ready_image
		image_ready_time = ready_image_time_usec

		ready_image = null
		ready_image_time_usec = 0
		has_ready_image = false

	mutex.unlock()

	if image_to_display != null:
		var wait_ms := (
			Time.get_ticks_usec() - image_ready_time
		) / 1000.0

		if wait_ms > 20.0:
			print("Image buffer wait: ", wait_ms, " ms")

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

		var start_time := Time.get_ticks_usec()

		var local_image := Image.create_from_data(
			current_frame["width"],
			current_frame["height"],
			false,
			Image.FORMAT_RGB8,
			current_frame["data"]
		)

		var elapsed_ms := (
			Time.get_ticks_usec() - start_time
		) / 1000.0

		print("Image processing: ", elapsed_ms, " ms")

		mutex.lock()

		# Keep only the newest processed image.
		ready_image = local_image
		ready_image_time_usec = Time.get_ticks_usec()
		has_ready_image = true

		mutex.unlock()


func _update_display_texture(new_image: Image) -> void:
	var now := Time.get_ticks_usec()

	if last_display_time_usec != 0:
		var interval_ms := (
			now - last_display_time_usec
		) / 1000.0

		if interval_ms > 100.0:
			print("Texture update interval: ", interval_ms, " ms")

	last_display_time_usec = now

	var start_time := Time.get_ticks_usec()

	if camera_texture == null:
		camera_texture = ImageTexture.create_from_image(new_image)
		texture = camera_texture
	else:
		camera_texture.update(new_image)

	var elapsed_ms := (
		Time.get_ticks_usec() - start_time
	) / 1000.0

	print("Texture update: ", elapsed_ms, " ms")

#Godot v4.7.1.stable - Ubuntu 22.04.5 LTS 22.04 on Wayland - X11 display driver, Multi-window, 1 monitor - OpenGL 3 (Compatibility) - llvmpipe (LLVM 15.0.7, 128 bits) -  (6 threads) - 7.73 GiB memory - PulseAudio (44100 Hz, Stereo/mono)
func _exit_tree() -> void:
	mutex.lock()
	is_running = false
	mutex.unlock()

	semaphore.post()

	if thread and thread.is_started():
		thread.wait_to_finish()

	if SignalBus.incoming_video.is_connected(on_incoming_video_signal):
		SignalBus.incoming_video.disconnect(on_incoming_video_signal)
