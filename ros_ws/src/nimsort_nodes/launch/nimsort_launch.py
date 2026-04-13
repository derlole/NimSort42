from launch import LaunchDescription
from launch_ros.actions import Node

WORLD_FRAME = "world"
ROBOT_FRAME = "robot"
CAMERA_FRAME = "camera"

WORLD_TO_ROBOT_TRANSLATION = (0.0, 0.0, 0.0) # x_r, y_r, z_r
WORLD_TO_ROBOT_RPY = (0.0, 0.0, 0.0) # roll_r, pitch_r, yaw_r

ROBOT_TO_CAMERA_TRANSLATION = (-0.2, 0.0, 1.0)
ROBOT_TO_CAMERA_RPY = (-1.5708, 0.0, 0.0)


def create_tf_node(name, translation, rotation, parent, child):
    return Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name=name,
        arguments=[
            str(translation[0]),
            str(translation[1]),
            str(translation[2]),
            str(rotation[0]),
            str(rotation[1]),
            str(rotation[2]),
            parent,
            child,
        ],
    )

def generate_launch_description():
    return LaunchDescription([

        create_tf_node(
            "world_to_robot",
            WORLD_TO_ROBOT_TRANSLATION,
            WORLD_TO_ROBOT_RPY,
            WORLD_FRAME,
            ROBOT_FRAME,
        ),

        create_tf_node(
            "robot_to_camera",
            ROBOT_TO_CAMERA_TRANSLATION,
            ROBOT_TO_CAMERA_RPY,
            ROBOT_FRAME,
            CAMERA_FRAME,
        ),

    ])