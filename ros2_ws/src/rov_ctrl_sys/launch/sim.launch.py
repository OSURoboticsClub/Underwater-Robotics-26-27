from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    params_dir = PathJoinSubstitution([FindPackageShare('rov_ctrl_sys'), 'config'])

    return LaunchDescription([
        # Underwater 3D Graphics & Physics Simulator
        Node(
            package='rov_ctrl_sys',
            executable='underwater_sim',
            name='underwater_sim',
            output='screen',
            parameters=[
                {'width': 640},
                {'height': 480},
                {'fps': 30.0},
            ],
        ),

        # Keyboard to Servo Node (maps UI key presses to camera gimbal & lights)
        Node(
            package='rov_ctrl_sys',
            executable='keyboard_to_servo',
            name='keyboard_to_servo',
            output='screen',
        ),

        # Thruster Allocator Node (allocates 8 thrusters from /cmd_vel)
        Node(
            package='rov_ctrl_sys',
            executable='thruster_allocator',
            name='thruster_allocator',
            output='screen',
            parameters=[
                PathJoinSubstitution([params_dir, 'motors.yaml']),
            ],
        ),

        # Joy to Motor Node (translates /joy into /cmd_vel)
        Node(
            package='rov_ctrl_sys',
            executable='joy_to_motor',
            name='joy_to_motor',
            output='screen',
            parameters=[
                PathJoinSubstitution([params_dir, 'motors.yaml']),
            ],
        ),

        # Gamepad Joy Node (reads physical USB gamepad)
        Node(
            package='joy',
            executable='joy_node',
            name='joy_node',
            output='screen',
        ),
    ])
