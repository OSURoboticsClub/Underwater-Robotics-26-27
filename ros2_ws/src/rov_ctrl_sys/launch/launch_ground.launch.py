from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, GroupAction, DeclareLaunchArgument
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import PushRosNamespace
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    launch_dir = PathJoinSubstitution([FindPackageShare('rov_ctrl_sys'), 'launch'])

    return LaunchDescription([
        GroupAction([
            PushRosNamespace('ground'),
            IncludeLaunchDescription(
                PathJoinSubstitution([launch_dir, 'gamepad.launch.py']),
            ),
            IncludeLaunchDescription(
                PathJoinSubstitution([launch_dir, 'display.launch.py']),
            ),
        ]),
    ])
