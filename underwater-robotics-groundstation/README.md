This project requires Godot 4.7.1 - stable. And not the Mono release.


# Installing Godot
To install Godot and open the project you can run the ./open_godot_project.sh file int the Underwater folder.

Or follow the instructions below.

You need to download the Godot 4.7.1 standard version. which can be found here: https://godotengine.org/download/archive/4.7.1-stable/

To get the project to properly connect to Ros2, you must source Ros2 at the same time that you run godot.
The best way to do that is 

```bash
source /opt/ros/humble/setup.bash
/path/to/godot/download --editor
```
You must do this everytime you want to open Godot.

You then import the the project into Godot by selecting the folder.
Once its open you can run it and it will connect to Ros.



# Building the GDExtension
The extension 'ros2_for_godot', is already built for both arm and x86. But if you need to rebuild it for some reason, follow the instructions bellow.


In a terminal, go in to the Underwater-Robotics-26-27/underwater-robotics-groundstation/ros2-for-godot folder, and run the following commands:

```bash
source /opt/ros/humble/setup.bash   # Source ROS
./build.sh                          # Build the .so file
./create_addon.sh                   # Create the addon to add to godot
```

Under the addons folder remove the existing 'ros2_for_godot' folder.
This creates a zip file under build.
Unzip this into the addons folder.

If you had to rebuild the addon, don't push it to the repo unless you have a good reason to.