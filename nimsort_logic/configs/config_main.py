from nimsort_main.tf_world_robot import TransformWorldRobot

# main_logic
POSITION_UNCORN: tuple[float, float, float] = TransformWorldRobot.robot_to_world(-0.065,-0.135, 0.07)
POSITION_CAT: tuple[float, float, float] = TransformWorldRobot.robot_to_world(-0.165, -0.135, 0.07)
INITIAL_POSITION: tuple[float, float, float] = TransformWorldRobot.robot_to_world(-0.005,-0.074, 0.02)
Z_PRE_POST_PICK: float = 0.08
Z_PRE_POST_TF: float = TransformWorldRobot.robot_to_world_z(Z_PRE_POST_PICK)
Z_PICK: float = TransformWorldRobot.robot_to_world_z(0.095) 
GENERIC_PICK_PRE_POSITION: tuple[float, float, float] = TransformWorldRobot.robot_to_world(-0.01, -0.074, Z_PRE_POST_PICK)
SENTINEL: tuple[float, float, float] = (-1.0, -1.0, -1.0,-1)
ROBOT_REACH: float = TransformWorldRobot.robot_to_world_x(-0.26)

WORLD_TO_ROBOT_TRANSLATION: tuple[float, float, float] = (0.29, -0.04, 0.083) # muss das ncht ein Tupple sein? 0.083 unsicher 
ZERO_ROBOT_POSITION: tuple[float, float, float] = TransformWorldRobot.robot_to_world(0.0, 0.0, 0.0)