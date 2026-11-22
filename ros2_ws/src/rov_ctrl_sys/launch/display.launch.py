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

import platform

def generate_launch_description():
    # Get Users architecture and run appropariate ui
    extension = "x86_64"
    architecture = platform.machine()
    if architecture == 'aarch64' or architecture == 'arm64':
        extension = "arm64"

    return LaunchDescription([
        ExecuteProcess(
            cmd=[[
                '~/Underwater-Robotics-Current/underwater-robotics-groundstation/exports/'+ extension +'/GroundstationUI.' + extension + ' -- ' + 
                '--/image_raw:/ground/image_uncompressed '+
                '--/motor_command:/ground/motor_command '+
                '--/servo_command:/ground/servo_command '+
                '--/joy:/ground/joy '+
                '--/key_states:/ground/key_states '
                # Add remap arguments here with "--remap_from:remap_to"
                #example: '--/keyboard_to_servo:/ground/keyboard_to_servo ',
            ]],
            shell=True
        ),
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
        # RegisterEventHandler(
        #     OnProcessExit(
        #         target_action=display_node,
        #         on_exit=[
        #             LogInfo(msg=('User closed the display window')),
        #             EmitEvent(event=Shutdown(
        #                 reason='Display closed'))
        #         ]
        #     )
        # ),
        # RegisterEventHandler(
        #     OnShutdown(
        #         on_shutdown=[LogInfo(
        #             msg=['Launch was asked to shutdown: ', LocalSubstitution('event.reason')]
        #         )]
        #     )
        # ),
    ])
