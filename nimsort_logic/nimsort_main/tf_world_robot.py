# TF_CONFIG
WORLD_TO_ROBOT_TRANSLATION: tuple[float, float, float] = (0.29, -0.04, 0.083) # muss das ncht ein Tupple sein? 0.083 unsicher 

class TransformWorldRobot:
    @staticmethod
    def world_to_robot(x_w: float, y_w: float, z_w: float) -> tuple[float, float, float]:
        return (-(x_w - WORLD_TO_ROBOT_TRANSLATION[0]), -(y_w - WORLD_TO_ROBOT_TRANSLATION[1]), -(z_w - WORLD_TO_ROBOT_TRANSLATION[2]))

    @staticmethod
    def robot_to_world(x_r: float, y_r: float, z_r: float) -> tuple[float, float, float]:
        return (-x_r + WORLD_TO_ROBOT_TRANSLATION[0], -y_r + WORLD_TO_ROBOT_TRANSLATION[1], -z_r + WORLD_TO_ROBOT_TRANSLATION[2])
    @staticmethod
    def world_to_robot_x(x_w: float) -> float:
        return -(x_w - WORLD_TO_ROBOT_TRANSLATION[0])

    @staticmethod
    def robot_to_world_x(x_r: float) -> float:
        return -x_r + WORLD_TO_ROBOT_TRANSLATION[0]
    
    @staticmethod
    def world_to_robot_y(y_w: float) -> float:
        return -(y_w - WORLD_TO_ROBOT_TRANSLATION[1])
    
    @staticmethod
    def robot_to_world_y(y_r: float) -> float:
        return -y_r + WORLD_TO_ROBOT_TRANSLATION[1]
    
    @staticmethod
    def world_to_robot_z(z_w: float) -> float:
        return -(z_w - WORLD_TO_ROBOT_TRANSLATION[2])
    
    @staticmethod
    def robot_to_world_z(z_r: float) -> float:
        return -z_r + WORLD_TO_ROBOT_TRANSLATION[2]