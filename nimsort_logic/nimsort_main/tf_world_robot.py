from configs.config_main import WORLD_TO_ROBOT_TRANSLATION

class TransformWorldRobot:
    @staticmethod
    def world_to_robot(x_w: float, y_w: float, z_w: float) -> tuple[float, float, float]:
        return (x_w - WORLD_TO_ROBOT_TRANSLATION[0], y_w - WORLD_TO_ROBOT_TRANSLATION[1], z_w - WORLD_TO_ROBOT_TRANSLATION[2])
    
    @staticmethod
    def robot_to_world( x_r: float, y_r: float, z_r: float) -> tuple[float, float, float]:
        return (x_r + WORLD_TO_ROBOT_TRANSLATION[0], y_r + WORLD_TO_ROBOT_TRANSLATION[1], z_r + WORLD_TO_ROBOT_TRANSLATION[2])