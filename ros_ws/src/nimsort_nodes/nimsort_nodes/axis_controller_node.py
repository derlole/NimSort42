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

MAX_VELOCITY_X = 0.5
MAX_VELOCITY_Y = 0.5
MAX_VELOCITY_Z = 0.5
MAX_ACCELERATION_X = 0.01
MAX_ACCELERATION_Y = 0.01
MAX_ACCELERATION_Z = 0.01
POSITION_TOLERANCE_X = 0.0001
POSITION_TOLERANCE_Y = 0.0001
POSITION_TOLERANCE_Z = 0.0001
VELOCITY_TOLERANCE_X = 0.001
VELOCITY_TOLERANCE_Y = 0.001
VELOCITY_TOLERANCE_Z = 0.001
KP_X = 1.0
KP_Y = 1.0
KP_Z = 1.0
KD_X = 0.1
KD_Y = 0.1
KD_Z = 0.1
D_FILTER_ALPHA_X = 0.5
D_FILTER_ALPHA_Y = 0.5
D_FILTER_ALPHA_Z = 0.5
TF_X = 0.1
TF_Y = 0.1
TF_Z = 0.1

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
        #TODO wait for main node to execute init process
        self.init_process.start()
        self.main_state = AxisControllerStates.INITIALIZING_AXIS_HW

    def ax_state_initializing_axis_hw(self):
        x_acc, y_acc, z_acc = self.init_process.robot_values((self.last_robot_pos.pos_x, self.last_robot_pos.pos_y, self.last_robot_pos.pos_z))
        if self.init_process.finished:
            self.main_state = AxisControllerStates.INITIALIZING_AXIS_SW
        self.send_acceleration(x_acc, y_acc, z_acc)


    def ax_state_initializing_axis_sw(self):
        trajectrory_planner_x = TrajectoryPlanner(MAX_VELOCITY_X, MAX_ACCELERATION_X, POSITION_TOLERANCE_X, VELOCITY_TOLERANCE_X)
        trajectrory_planner_y = TrajectoryPlanner(MAX_VELOCITY_Y, MAX_ACCELERATION_Y, POSITION_TOLERANCE_Y, VELOCITY_TOLERANCE_Y)
        trajectrory_planner_z = TrajectoryPlanner(MAX_VELOCITY_Z, MAX_ACCELERATION_Z, POSITION_TOLERANCE_Z, VELOCITY_TOLERANCE_Z)

        controller_x = Controller(KP_X, KD_X, D_FILTER_ALPHA_X, TF_X, MAX_ACCELERATION_X, -MAX_ACCELERATION_X, True, True)
        controller_y = Controller(KP_Y, KD_Y, D_FILTER_ALPHA_Y, TF_Y, MAX_ACCELERATION_Y, -MAX_ACCELERATION_Y, True, True)
        controller_z = Controller(KP_Z, KD_Z, D_FILTER_ALPHA_Z, TF_Z, MAX_ACCELERATION_Z, -MAX_ACCELERATION_Z, True, True)

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

    def ax_state_running(self):
        pass

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