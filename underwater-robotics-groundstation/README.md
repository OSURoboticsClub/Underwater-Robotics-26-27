This project requires Godot 4.7.1 - stable. And not the Mono release.

Before opening the project you must first build the GDExtension 'ros2_for_godot'. 
But only if your device is x86_64, its already been built for arm64. And if you build it for x86_64, please push that to the branch.
If you're on ARM, skip to Installing Godot
In a terminal, go in to the ros2-for-godot  folder, and run the following commands:
```bash
source /opt/ros/humble/setup.bash
./build.sh                  # Release (default)
./create_addon.sh
```
This creates a zip file under build/
Unzip this and move the .so file from /ros2_for_godot/bin/    to   /addons/ros2_for_godot/bin/linux.x86_64/


# Installing Godot
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

Hopefully this worked and I didn't forget a step.
Scripts will be coming soon to help automate this process.