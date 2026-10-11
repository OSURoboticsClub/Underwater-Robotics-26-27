from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    params_dir = PathJoinSubstitution([FindPackageShare('rov_ctrl_sys'), 'config'])

    return LaunchDescription([
        Node(
            package='rov_ctrl_sys',
            executable='joy_to_motor',
            name='joy_to_motor',
            output='log',
#             ros_arguments=['--log-level', 'debug'],
            parameters=[
                PathJoinSubstitution([params_dir, 'motors.yaml']),
            ],
#             ros_arguments=['--params-file', PathJoinSubstitution([params_dir, 'motors.yaml'])],
        ),
        Node(
            package='rov_ctrl_sys',
            executable='joy_to_servo',
            name='joy_to_servo',
            output='log',
#             ros_arguments=['--log-level', 'debug'],
        ),
        Node(
            package='joy',
            executable='joy_node',
            name='gamepad',
        ),
    ])
