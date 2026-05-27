from nimsort_main.tf_world_robot import TransformWorldRobot

# main_logic
POSITION_UNCORN: tuple[float, float, float] = TransformWorldRobot.robot_to_world(-0.16,-0.14, 0.07)
POSITION_CAT: tuple[float, float, float] = TransformWorldRobot.robot_to_world(-0.06, -0.14, 0.07)
INITIAL_POSITION: tuple[float, float, float] = TransformWorldRobot.robot_to_world(-0.01,-0.05, 0.02)
Z_PRE_POST_PICK: float = 0.08 
Z_PICK: float = TransformWorldRobot.robot_to_world_z(0.095) 
GENERIC_PICK_PRE_POSITION: tuple[float, float, float] = TransformWorldRobot.robot_to_world(-0.01, -0.05, Z_PRE_POST_PICK)
SENTINEL: tuple[float, float, float] = (-1.0, -1.0, -1.0,-1)
ROBOT_REACH: float = -0.3

# TF_CONFIG
WORLD_TO_ROBOT_TRANSLATION: float = (0.29, -0.04, 0.083)

