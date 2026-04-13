import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException

from ro45_portalrobot_interfaces.msg import RobotCmd

import sys
import termios
import tty
import select

START_VALUE = 0.0
INCREMENT = 0.005
DURATION_STEPS = 10   # Anzahl Timer-Zyklen (0.1s pro Zyklus)


class AxisControllerHand(Node):
    def __init__(self):
        super().__init__('axis_hand_drive_node')

        self.current_acceleration = START_VALUE

        self.state = "IDLE"
        self.counter = 0

        self.robot_cmd_pub = self.create_publisher(
            RobotCmd,
            'robot_command',
            10
        )

        self.timer = self.create_timer(
            0.1,
            self.main_loop_callback
        )

    def send_acceleration(self, acc):
        msg = RobotCmd()
        msg.accel_x = 0.0
        msg.accel_y = -acc
        msg.accel_z = 0.0
        self.robot_cmd_pub.publish(msg)

    def main_loop_callback(self):
        # nur reagieren, wenn Test läuft
        if self.state != "ACCEL":
            return

        self.send_acceleration(self.current_acceleration)
        self.counter += 1

        if self.counter >= DURATION_STEPS:
            self.send_acceleration(0.0)
            self.state = "DONE"
            self.get_logger().info(
                f"Test fertig mit acceleration: {self.current_acceleration}"
            )

    def start_test(self):
        if self.state != "IDLE":
            self.get_logger().warn("Test läuft bereits oder ist beendet.")
            return

        self.current_acceleration += INCREMENT
        self.get_logger().info(
            f"Starte Test mit acceleration: {self.current_acceleration}"
        )

        self.counter = 0
        self.state = "ACCEL"


def main(args=None):
    rclpy.init(args=args)
    node = AxisControllerHand()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    print("\n--- Steuerung ---")
    print("i → Test starten")
    print("Ctrl+C → Beenden\n")

    try:
        tty.setcbreak(fd)

        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.1)

            rlist, _, _ = select.select([sys.stdin], [], [], 0.1)

            if rlist:
                key = sys.stdin.read(1)

                if key == 'i':
                    node.start_test()

    except (ExternalShutdownException, KeyboardInterrupt):
        node.get_logger().info("Shutting down AxisController node.")

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        node.send_acceleration(0.0)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()