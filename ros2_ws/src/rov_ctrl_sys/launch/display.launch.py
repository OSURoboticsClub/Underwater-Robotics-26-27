from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    SetEnvironmentVariable,
    EmitEvent,
    ExecuteProcess,
    LogInfo,
    RegisterEventHandler,
    TimerAction
)
from launch.conditions import IfCondition
from launch.event_handlers import (
    OnExecutionComplete,
    OnProcessExit,
    OnProcessIO,
    OnProcessStart,
    OnShutdown
)
from launch.events import Shutdown
from launch.substitutions import (
    EnvironmentVariable,
    FindExecutable,
    LaunchConfiguration,
    LocalSubstitution,
    PathJoinSubstitution,
    PythonExpression
)
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node

def generate_launch_description():
    params_dir = PathJoinSubstitution([FindPackageShare('rov_ctrl_sys'), 'config'])
    fullscreen = LaunchConfiguration('fullscreen')

    display_node = Node(
        package='rov_ctrl_sys',
        executable='window',
        name='display',
        output='log',
        parameters=[
            {'fullscreen': LaunchConfiguration('fullscreen')},
            PathJoinSubstitution([params_dir, 'camera_shared.yaml']),
        ],
        remappings=[
            ('image_raw','image_uncompressed'),
        ],
#         ros_arguments=['--log-level', 'debug'],
    )

    return LaunchDescription([
        DeclareLaunchArgument('fullscreen', default_value=fullscreen),
        display_node,
        Node(
            package='rov_ctrl_sys',
            executable='keyboard_to_servo',
            name='keyboard_to_servo',
            output='log',
#             ros_arguments=['--log-level', 'debug'],
        ),
        Node(
            package='image_transport',
            executable='republish',
            name='camera_uncompressor',
            remappings=[
                ('in/compressed', '/rov/image_raw/compressed'),
                ('out', '/ground/image_uncompressed'),
            ],
            arguments=[
                'compressed', 'raw', 
            ],
            output='log'
        ),
#         Node(
#             package='rov_ctrl_sys',
#             executable='crab_detect',
#             name='crab_detect',
#             remappings=[
#                 ('image_raw', 'image_uncompressed'),
#             ],
#             output='log',
#         ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=display_node,
                on_exit=[
                    LogInfo(msg=('User closed the display window')),
                    EmitEvent(event=Shutdown(
                        reason='Display closed'))
                ]
            )
        ),
        RegisterEventHandler(
            OnShutdown(
                on_shutdown=[LogInfo(
                    msg=['Launch was asked to shutdown: ', LocalSubstitution('event.reason')]
                )]
            )
        ),
    ])
