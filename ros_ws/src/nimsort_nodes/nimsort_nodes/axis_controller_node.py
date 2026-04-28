import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor

from nimsort_motion.axis import Axis
from nimsort_motion.controller import Controller
from nimsort_motion.trajectroy_planner import TrajectoryPlanner
from nimsort_msgs.msg import NimSortMotionState, NimSortTarget
from nimsort_motion.axis_controller_states import AxisControllerStates
from nimsort_motion.init_process import InitProcess
from ro45_portalrobot_interfaces.msg import RobotCmd, RobotPos

MAX_VELOCITY_X = 0.05
MAX_VELOCITY_Y = 0.05
MAX_VELOCITY_Z = 0.05
MAX_ACCELERATION_X = 0.02
MAX_ACCELERATION_Y = 0.02
MAX_ACCELERATION_Z = 0.02
POSITION_TOLERANCE_X = 0.0001
POSITION_TOLERANCE_Y = 0.0001
POSITION_TOLERANCE_Z = 0.0001
VELOCITY_TOLERANCE_X = 0.001
VELOCITY_TOLERANCE_Y = 0.001
VELOCITY_TOLERANCE_Z = 0.001
KP_X = 1.419
KP_Y = 1.419
KP_Z = 1.519
KD_X = 4.92
KD_Y = 4.92
KD_Z = 4.92
D_FILTER_ALPHA_X = 0.5
D_FILTER_ALPHA_Y = 0.5
D_FILTER_ALPHA_Z = 0.5
TF_X = 0.00875
TF_Y = 0.00875
TF_Z = 0.00875

class AxisController(Node):
    def __init__(self):
        super().__init__('nimsort_axis_controller_node')

        self.last_robot_pos = None
        self.last_nimsort_target = None
        self.main_state = AxisControllerStates.EMPTY
        self.init_process = InitProcess()
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.offset_z = 0.0

        self.axis_x = None
        self.axis_y = None
        self.axis_z = None

        self.nimsort_target_sub = self.create_subscription(
            NimSortTarget,
            '/NimSortTarget',
            self.nimsort_target_callback,
            10
        )
        self.robot_pos_sub = self.create_subscription(
            RobotPos,
            'robot_position',
            self.robot_pos_callback,
            10
        )
        self.motion_state_pub = self.create_publisher(
            NimSortMotionState,
            '/NimSortMotionState',
            10
        )
        self.robot_cmd_pub = self.create_publisher(
            RobotCmd,
            'robot_command',
            10
        )

        self.timer = self.create_timer(
            0.1,
            self.main_order
        )

    def send_acceleration(self, acc_x, acc_y, acc_z):
        msg = RobotCmd()
        msg.accel_x = acc_x
        msg.accel_y = acc_y
        msg.accel_z = acc_z
        self.robot_cmd_pub.publish(msg)

    def main_order(self):
        match self.main_state:
            case AxisControllerStates.EMPTY:
                self.get_logger().info("State: EMPTY")
                self.ax_state_empty()

            case AxisControllerStates.INITIALIZING_AXIS_HW:
                self.get_logger().info("State: INITIALIZING_AXIS_HW")
                self.ax_state_initializing_axis_hw()

            case AxisControllerStates.INITIALIZING_AXIS_SW:
                self.ax_state_initializing_axis_sw()

            case AxisControllerStates.RUNNING:
                self.ax_state_running()
            

    def nimsort_target_callback(self, msg):
        self.last_nimsort_target = msg
        self.get_logger().info(f"Received NimSortTarget: {msg}")

    def robot_pos_callback(self, msg):
        self.last_robot_pos = msg
        self.get_logger().info(f"Received RobotPos: {msg}")

    def ax_state_empty(self):
        if self.last_nimsort_target is not None and self.last_nimsort_target.process_id == 1:
            self.init_process.start()
            self.main_state = AxisControllerStates.INITIALIZING_AXIS_HW

    def ax_state_initializing_axis_hw(self):
        x_acc, y_acc, z_acc = self.init_process.robot_values((self.last_robot_pos.pos_x, self.last_robot_pos.pos_y, self.last_robot_pos.pos_z))
        if self.init_process.finished:
            self.main_state = AxisControllerStates.INITIALIZING_AXIS_SW
        self.send_acceleration(x_acc, y_acc, z_acc)


    def ax_state_initializing_axis_sw(self):
        trajectrory_planner_x = TrajectoryPlanner(MAX_VELOCITY_X, MAX_ACCELERATION_X)
        trajectrory_planner_y = TrajectoryPlanner(MAX_VELOCITY_Y, MAX_ACCELERATION_Y)
        trajectrory_planner_z = TrajectoryPlanner(MAX_VELOCITY_Z, MAX_ACCELERATION_Z)

        controller_x = Controller(KP_X, KD_X, MAX_ACCELERATION_X, TF_X)
        controller_y = Controller(KP_Y, KD_Y, MAX_ACCELERATION_Y, TF_Y)
        controller_z = Controller(KP_Z, KD_Z, MAX_ACCELERATION_Z, TF_Z)

        self.axis_x = Axis("X", controller_x, trajectrory_planner_x)
        self.axis_y = Axis("Y", controller_y, trajectrory_planner_y)
        self.axis_z = Axis("Z", controller_z, trajectrory_planner_z)

        self.offset_x = self.last_robot_pos.pos_x
        self.offset_y = self.last_robot_pos.pos_y
        self.offset_z = self.last_robot_pos.pos_z
        
        self.get_logger().info(f"[ACN-][ax_in_sw]: X Axis: {self.axis_x}")
        self.get_logger().info(f"[ACN-][ax_in_sw]: Y Axis: {self.axis_y}")
        self.get_logger().info(f"[ACN-][ax_in_sw]: Z Axis: {self.axis_z}")

        self.main_state = AxisControllerStates.RUNNING

    def publish_motion_state(self, reached, gripper_active):
        msg = NimSortMotionState()
        msg.reached = reached
        msg.gripper_active = gripper_active
        self.motion_state_pub.publish(msg)

    def ax_state_running(self):
        print(f"[ACN-][ax_run]: Last Robot Pos: {self.axis_x.target_reached}, {self.axis_y.target_reached}, {self.axis_z.target_reached}")
        if (self.axis_x.target_reached and self.axis_y.target_reached and self.axis_z.target_reached) and self.last_nimsort_target is not None:
            self.publish_motion_state(True, False)

        self.axis_x.set_target(self.last_nimsort_target.target_point.x)
        self.axis_y.set_target(self.last_nimsort_target.target_point.y)
        self.axis_z.set_target(self.last_nimsort_target.target_point.z)

        acc_x = self.axis_x.update(self.last_robot_pos.pos_x - self.offset_x, 0.1) #TODO dt as timestamp difference actually calculated
        acc_y = self.axis_y.update(self.last_robot_pos.pos_y - self.offset_y, 0.1)
        acc_z = self.axis_z.update(self.last_robot_pos.pos_z - self.offset_z, 0.1)

        self.send_acceleration(acc_x, acc_y, acc_z)

def main(args=None):
    rclpy.init(args=args)
    node = AxisController()

    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except (ExternalShutdownException, KeyboardInterrupt):
        node.get_logger().error("[ACN-][main----]: Shutdown Node")

    finally:
        executor.shutdown()
        rclpy.shutdown()


if __name__ == '__main__':
    main()