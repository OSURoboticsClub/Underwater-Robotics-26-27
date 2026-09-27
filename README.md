# Underwater-Robotics-26-27
Code for the Underwater Robotics subteam of DAM Robotics at Oregon State University

The code/scripts in this repository assume they are located inside the user's home
directory, inside a folder called "Underwater-Robotics-Current". Not inside "Underwater-Robotics-26-27".
This is so that the files do not need to be updated every time the repository name changes.

The intended method is to create a symlink named Underwater-Robotics-Current that points to the repo. On Linux, you can
use "ln -s ./Path/To/The/Repo/Underwater-Robotics-26-27 ~/Underwater-Robotics-Current" to create such a symlink.

To run the code, use "ros2 launch rov_ctrl_sys launch_ground.launch.py" on the ground station and "ros2 launch rov_ctrl_sys launch_rov.launch.py".

To upload code to the esps over ssh, use a variation on the following commands:
arduino-cli compile --fqbn esp32:esp32:esp32da ~/Underwater-Robotics-Current/esp-32-code/servos-sensors/servos-sensors.ino
arduino-cli upload -p /dev/usb_right --fqbn esp32:esp32:esp32da ~/Underwater-Robotics-Current/esp-32-code/servos-sensors/servos-sensors.ino

These commands (or variations) can be used to help setup automatic detection and naming of specific usb devices
udevadm info --attribute-walk --name=/dev/video2 > video2.txt
sudo udevadm control --reload-rules
sudo udevadm trigger
