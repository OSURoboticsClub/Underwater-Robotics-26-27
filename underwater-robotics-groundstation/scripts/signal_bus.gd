extends Node

## Send out parsed ROS2 data to be displayed.
@warning_ignore("unused_signal")
signal incoming_data(data: Dictionary[String, Variant])

## Send out the incoming data for a video feed.
@warning_ignore("unused_signal")
signal incoming_video(image_data)

## This signal is emitted when the code encounters an error
## that won't break the project but should be fixed.
## And it dispalys it in the running UI.
@warning_ignore("unused_signal")
signal error(error_text: String)


@warning_ignore("unused_signal")
signal outgoing_data(pub_name: String, data: Dictionary[String, Variant])
