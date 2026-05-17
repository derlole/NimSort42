from enum import Enum

class ProcessId(Enum):
    """"Enum für die process ids zwischen Main und Axis Controller"""
    SELF_INIT = 0
    INIT_AXIS = 1
    GO_TO_POS = 2
    PICKING_DRIVE = 3
    GO_TO_POS_WITH_GRIPPER = 4
    DEACTIVATE_GRIPPER = 5