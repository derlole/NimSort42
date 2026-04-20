import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor

from nimsort_msgs.msg import NimSortMotionState, NimSortTarget
from nimsort_motion.axis_controller_states import AxisControllerStates
from nimsort_motion.init_process import InitProcess
from ro45_portalrobot_interfaces.msg import RobotCmd, RobotPos

class AxisController(Node):
    def __init__(self):
        super().__init__('nimsort_axis_controller_node')

        self.last_robot_pos = None
        self.last_nimsort_target = None
        self.main_state = AxisControllerStates.EMPTY
        self.init_process = InitProcess()

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
        self.init_process.start()
        self.main_state = AxisControllerStates.INITIALIZING_AXIS_HW

    def ax_state_initializing_axis_hw(self):
        x_acc, y_acc, z_acc = self.init_process.robot_values((self.last_robot_pos.pos_x, self.last_robot_pos.pos_y, self.last_robot_pos.pos_z))
        if self.init_process.finished:
            self.main_state = AxisControllerStates.INITIALIZING_AXIS_SW
        self.send_acceleration(x_acc, y_acc, z_acc)


    def ax_state_initializing_axis_sw(self):
        pass

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