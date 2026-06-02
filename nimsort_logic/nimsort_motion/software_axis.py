import time
from nimsort_motion.axis import Axis
from nimsort_motion.controller import Controller
from nimsort_motion.trajectroy_planner import TrajectoryPlanner
from nimsort_main.tf_world_robot import TransformWorldRobot
from nimsort_main.process_id import ProcessId
from configs.config_axis import *

class SoftwareAxis:
    def __inti__(self):
        trajectrory_planner_x = TrajectoryPlanner(MAX_VELOCITY_X, MAX_ACCELERATION_X, POSITION_TOLERANCE_X, VELOCITY_TOLERANCE_X)
        trajectrory_planner_y = TrajectoryPlanner(MAX_VELOCITY_Y, MAX_ACCELERATION_Y, POSITION_TOLERANCE_Y, VELOCITY_TOLERANCE_Y)
        trajectrory_planner_z = TrajectoryPlanner(MAX_VELOCITY_Z, MAX_ACCELERATION_Z, POSITION_TOLERANCE_Z, VELOCITY_TOLERANCE_Z)

        controller_x = Controller(KP_X, KD_X, MAX_ACCELERATION_X, TF_X)
        controller_y = Controller(KP_Y, KD_Y, MAX_ACCELERATION_Y, TF_Y)
        controller_z = Controller(KP_Z, KD_Z, MAX_ACCELERATION_Z, TF_Z)

        self.axis_x = Axis("X", controller_x, trajectrory_planner_x)
        self.axis_y = Axis("Y", controller_y, trajectrory_planner_y)
        self.axis_z = Axis("Z", controller_z, trajectrory_planner_z)

        self.offset_x = 0.0
        self.offset_y = 0.0
        self.offset_z = 0.0

    def reached(self, process_id):
        if process_id == ProcessId.PICKING_DRIVE.value:
            return self.axis_z.target_reached and self.axis_y.target_reached
        
        return self.axis_x.target_reached and self.axis_y.target_reached and self.axis_z.target_reached

    def gripper_active(self, process_id: int):
        return process_id == ProcessId.PICKING_DRIVE.value or process_id == ProcessId.GO_TO_POS_WITH_GRIPPER.value

    def set_target(self, x: float , y: float , z: float):
        target_trafo_x, target_trafo_y, target_trafo_z = TransformWorldRobot.world_to_robot(x, y, z)
        
        self.axis_x.set_target(target_trafo_x * 0.8)
        self.axis_y.set_target(target_trafo_y * 0.8)
        self.axis_z.set_target(target_trafo_z)

    def update(self, pos_x: float, pos_y:float, pos_z: float, dt: float):
        acc_x = self.axis_x.update(pos_x - self.offset_x, dt)
        acc_y = self.axis_y.update(pos_y - self.offset_y, dt)
        acc_z = self.axis_z.update(pos_z - self.offset_z, dt)

        return acc_x, acc_y, acc_z 
    
    def set_offset(self, x: float, y: float, z: float):
        self.offset_x = x
        self.offset_y = y
        self.offset_z = z