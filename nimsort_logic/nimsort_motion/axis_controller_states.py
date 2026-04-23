from enum import Enum

class AxisControllerStates(Enum):
    """States for the axis controller."""
    EMPTY = 0 #gripper empty ?
    INITIALIZING_AXIS_HW = 1
    INITIALIZING_AXIS_SW = 2
    RUNNING = 3