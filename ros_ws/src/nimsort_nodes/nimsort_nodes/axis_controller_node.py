import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup 

from nimsort_msgs.msg import NimSortMotionState, NimSortTarget
from nimsort_motion.axis import Axis, AxisState
from nimsort_motion.axis_interaface import AxisInterface 

from ro45_portalrobot_interfaces.msg import RobotCmd, RobotPos

class AxisController(Node):
    def __int__(self):
        super().__init__('nimsort_axis_controller_node')

        self._x_axis = None
        self._y_axis = None
        self._z_axis = None

        self.last_robot_pos = None
        self.last_nimsort_target = None

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
        self.timer = self.create_timer(0.1, self.main_loop_callback, MutuallyExclusiveCallbackGroup())

    def main_loop_callback(self):
        pass

    def nimsort_target_callback(self, msg: NimSortTarget):
        # self.get_logger().info(f"Received new NimSortTarget: {msg}")
        self.last_nimsort_target = msg

    def robot_pos_callback(self, msg: RobotPos):
        # self.get_logger().info(f"Received new RobotPos: {msg}")
        self.last_robot_pos = msg


def main(args=None):
    rclpy.init(args=args)
    node = AxisController()
    executor = MultiThreadedExecutor()

    try:
        rclpy.spin(node, executor=executor)
    except (ExternalShutdownException, KeyboardInterrupt):
        node.get_logger().info("Shutting down AxisController node.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()