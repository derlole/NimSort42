import math

from launch import LaunchDescription
from launch_ros.actions import Node

WORLD_FRAME = "world"
ROBOT_FRAME = "robot"
CAMERA_FRAME = "camera"

WORLD_TO_ROBOT_TRANSLATION = (0.29, -0.04, 0.083)  # x_r, y_r, z_r
WORLD_TO_ROBOT_RPY = (0.0, 0.0, 0.0)          # roll_r, pitch_r, yaw_r

WORLD_PITCH_ANGLE_DEG = 32.7
CAMERA_TO_WORLD_TRANSLATION = (0.321, 0.037, -0.489)
CAMERA_TO_WORLD_RPY = (0.0, -(WORLD_PITCH_ANGLE_DEG * (math.pi/180)), 0.0)


def generate_launch_description():
    return LaunchDescription([

        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="world_to_robot",
            arguments=[
                str(WORLD_TO_ROBOT_TRANSLATION[0]),
                str(WORLD_TO_ROBOT_TRANSLATION[1]),
                str(WORLD_TO_ROBOT_TRANSLATION[2]),
                str(WORLD_TO_ROBOT_RPY[0]),
                str(WORLD_TO_ROBOT_RPY[1]),
                str(WORLD_TO_ROBOT_RPY[2]),
                WORLD_FRAME,
                ROBOT_FRAME,
            ],
        ),

        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="camera_to_world",
            arguments=[
                str(CAMERA_TO_WORLD_TRANSLATION[0]),
                str(CAMERA_TO_WORLD_TRANSLATION[1]),
                str(CAMERA_TO_WORLD_TRANSLATION[2]),
                str(CAMERA_TO_WORLD_RPY[0]),
                str(CAMERA_TO_WORLD_RPY[1]),
                str(CAMERA_TO_WORLD_RPY[2]),
                CAMERA_FRAME,
                WORLD_FRAME,
            ],
        ),

    ])