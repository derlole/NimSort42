import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor

from nimsort_msgs.msg import NimSortMotionState, NimSortTarget
from ro45_portalrobot_interfaces.msg import RobotCmd, RobotPos

class AxisController(Node):
    def __init__(self):
        super().__init__('nimsort_axis_controller_node')

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

        self.timer = self.create_timer(
            0.1,
            self.main_order
        )

    def send_acceleration(self, acc):
        msg = RobotCmd()
        #TODO fill msg
        self.robot_cmd_pub.publish(msg)

    def main_order(self):
        pass

    def nimsort_target_callback(self, msg):
        self.last_nimsort_target = msg
        self.get_logger().info(f"Received NimSortTarget: {msg}")

    def robot_pos_callback(self, msg):
        self.last_robot_pos = msg
        self.get_logger().info(f"Received RobotPos: {msg}")

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