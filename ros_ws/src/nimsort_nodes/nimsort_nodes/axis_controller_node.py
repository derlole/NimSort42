import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup 

from nimsort_msgs.msg import NimSortMotionState, NimSortTarget
from ro45_portalrobot_interfaces.msg import RobotCmd, RobotPos

import threading
import sys
import termios
import tty

START_VALUE = 0.0
INCREMENT = 0.1
STEPS_PER_PHASE = 10 


class AxisController(Node):
    def __init__(self):
        super().__init__('nimsort_axis_controller_node')

        self.last_robot_pos = None
        self.last_nimsort_target = None

        self.current_acceleration = START_VALUE

        self.state = "IDLE"
        self.counter = 0

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
            self.main_loop_callback,
            callback_group=MutuallyExclusiveCallbackGroup()
        )

        threading.Thread(target=self.keyboard_listener, daemon=True).start()

    def send_acceleration(self, acc): #TODO this is a temporary funciton to controll onöy one axis at a time manually
        msg = RobotCmd()

        msg.accel_x = acc
        msg.accel_y = 0.0
        msg.accel_z = 0.0

        self.robot_cmd_pub.publish(msg)

    def main_loop_callback(self):
        if self.state == "IDLE":
            return

        elif self.state == "ACCEL_FORWARD":
            self.send_acceleration(self.current_acceleration)
            self.counter += 1

            if self.counter >= STEPS_PER_PHASE:
                self.counter = 0
                self.state = "ACCEL_BACKWARD"

        elif self.state == "ACCEL_BACKWARD":
            self.send_acceleration(-self.current_acceleration)
            self.counter += 1

            if self.counter >= STEPS_PER_PHASE:
                self.counter = 0
                self.state = "IDLE"
                self.get_logger().info(
                    f"Test fertig mit acceleration: {self.current_acceleration}"
                )

    def keyboard_listener(self):
        while True:
            key = self.get_key()

            if key == 'i':
                self.current_acceleration += INCREMENT
                self.get_logger().info(
                    f"Starte Test mit acceleration: {self.current_acceleration}"
                )
                self.state = "ACCEL_FORWARD"
                self.counter = 0

    def get_key(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def nimsort_target_callback(self, msg):
        self.last_nimsort_target = msg

    def robot_pos_callback(self, msg):
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