from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    serial_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ro45_ros2_pickrobot_serial'),
                'launch',
                'launch_nodes.py'
            )
        )
    )
    camera_index = LaunchConfiguration('camera_index', default='4')

    return LaunchDescription([

        serial_launch,

        DeclareLaunchArgument(
            'camera_index',
            default_value='4',
            description='Index of the camera to use'
        ),
        Node(
            package='nimsort_nodes',
            executable='nimsort_axis_controller',
            name='nimsort_axis_controller',
            output='screen'
        ),
        Node(
            package='nimsort_nodes',
            executable='nimsort_position_prediction',
            name='nimsort_position_prediction',
            output='screen'
        ),
        Node(
            package='nimsort_nodes',
            executable='nimsort_vision',
            name='nimsort_vision',
            output='screen',
            parameters=[{'camera_index': camera_index}]
        ),
        Node(
            package='nimsort_nodes',
            executable='nimsort_main',
            name='nimsort_main',
            output='screen'
        )
    ])