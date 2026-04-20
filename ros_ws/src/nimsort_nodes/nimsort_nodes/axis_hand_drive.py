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

        self.current_acceleration = (-0.007, -0.007, 0.007)

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

    def send_acceleration(self, acc_x, acc_y, acc_z):
        msg = RobotCmd()
        msg.accel_x = acc_x
        msg.accel_y = acc_y
        msg.accel_z = acc_z
        self.robot_cmd_pub.publish(msg)

    def main_loop_callback(self):
        if self.state != "ACCEL":
            return

        # Phase 1: Beschleunigung
        if self.counter < DURATION_STEPS:
            self.send_acceleration(self.current_acceleration[0], self.current_acceleration[1], self.current_acceleration[2])

        # Phase 2: Gegenbeschleunigung
        elif self.counter < 2 * DURATION_STEPS:
            self.send_acceleration(
                -self.current_acceleration[0],
                -self.current_acceleration[1],
                -self.current_acceleration[2],
            )

        # Fertig
        else:
            self.send_acceleration(0.0, 0.0, 0.0)
            self.state = "DONE"
            self.get_logger().info(
                f"Test fertig mit acceleration: {self.current_acceleration}"
            )
            return

        self.counter += 1

    def start_test(self):
        if self.state != "IDLE":
            self.get_logger().warn("Test läuft bereits oder ist beendet.")
            return

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
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()