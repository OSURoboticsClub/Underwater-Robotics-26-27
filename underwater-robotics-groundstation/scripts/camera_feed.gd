extends TextureRect

var camera_texture: ImageTexture
# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	SignalBus.incoming_video.connect(display)


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass

func display(image_msg) -> void:
	_on_camera_image(image_msg)
	#texture = create_camera_texture(image_msg)
	#var txtre = convert_ros_image(image_msg)
	#print(typeof(image_msg))
	if image_msg == null:
		SignalBus.error.emit("An image was not supplied")


func _on_camera_image(msg):
	var start := Time.get_ticks_usec()

	var image: Image = convert_ros_image(msg)

	var after_conversion := Time.get_ticks_usec()

	if image == null:
		return

	if camera_texture == null:
		camera_texture = ImageTexture.create_from_image(image)
	else:
		camera_texture.update(image)

	var after_texture := Time.get_ticks_usec()

	print(
		"Conversion: ",
		(after_conversion - start) / 1000.0,
		" ms | Texture: ",
		(after_texture - after_conversion) / 1000.0,
        " ms"
	)

	
	#camera_frame_received.emit(camera_texture)
	texture = camera_texture


func convert_ros_image(msg) -> Image:
	var width: int = msg.width
	var height: int = msg.height
	var encoding: String = msg.encoding
	var data: PackedByteArray = msg.data

	if width <= 0 or height <= 0:
		push_warning("Invalid camera image dimensions")
		return null

	if encoding != "rgb8" and encoding != "bgr8":
		push_warning("Unsupported image encoding: " + encoding)
		return null

	var expected_size: int = width * height * 3

	if data.size() < expected_size:
		push_warning("Camera image data is smaller than expected")
		return null

	if encoding == "bgr8":
		data = data.duplicate()

		for i in range(0, expected_size, 3):
			var temp: int = data[i]
			data[i] = data[i + 2]
			data[i + 2] = temp

	var image := Image.create_from_data(
		width,
		height,
		false,
		Image.FORMAT_RGB8,
		data
	)

	return image

func create_camera_texture(msg) -> ImageTexture:
	var image: Image = convert_ros_image(msg)

	if image == null:
		return null

	if camera_texture == null:
		camera_texture = ImageTexture.create_from_image(image)
	else:
		camera_texture.update(image)

	return camera_texture
