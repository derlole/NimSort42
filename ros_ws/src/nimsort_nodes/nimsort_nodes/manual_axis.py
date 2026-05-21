import sys
import time
import termios
import tty
import select

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor, ExternalShutdownException

from nimsort_motion.axis import Axis
from nimsort_motion.controller import Controller
from nimsort_motion.trajectroy_planner import TrajectoryPlanner
from nimsort_motion.axis_controller_states import AxisControllerStates
from nimsort_motion.init_process import InitProcess

from ro45_portalrobot_interfaces.msg import RobotCmd, RobotPos


MAX_VELOCITY_X = 0.1
MAX_VELOCITY_Y = 0.1
MAX_VELOCITY_Z = 0.1

MAX_ACCELERATION_X = 0.02
MAX_ACCELERATION_Y = 0.02
MAX_ACCELERATION_Z = 0.02

POSITION_TOLERANCE_X = 0.001
POSITION_TOLERANCE_Y = 0.001
POSITION_TOLERANCE_Z = 0.001

VELOCITY_TOLERANCE_X = 0.001
VELOCITY_TOLERANCE_Y = 0.001
VELOCITY_TOLERANCE_Z = 0.001

KP_X = 1.2
KP_Y = 1.2
KP_Z = 1.2

KD_X = 2.3
KD_Y = 2.3
KD_Z = 2.3

TF_X = 0.00875
TF_Y = 0.00875
TF_Z = 0.00875

STEP_SIZE = 0.01
FINE_STEP = 0.001


class ManualAxisController(Node):

    def __init__(self):
        super().__init__('manual_axis_controller')

        self.main_state = AxisControllerStates.EMPTY

        self.last_robot_pos = None
        self.last_robot_pos_time = time.time()

        self.init_process = InitProcess()

        self.axis_x = None
        self.axis_y = None
        self.axis_z = None

        self.offset_x = 0.0
        self.offset_y = 0.0
        self.offset_z = 0.0

        self.target_x = 0.0
        self.target_y = 0.0
        self.target_z = 0.0

        self.last_update_time = time.monotonic()
        self.last_state = None
        self.waiting_for_robot_position = True

        self.robot_pos_sub = self.create_subscription(
            RobotPos,
            'robot_position',
            self.robot_pos_callback,
            10
        )

        self.robot_cmd_pub = self.create_publisher(
            RobotCmd,
            'robot_command',
            10
        )

        self.get_logger().info("[MANUAL]: Subscriber auf 'robot_position' erstellt")
        self.get_logger().info("[MANUAL]: Publisher auf 'robot_command' erstellt")

        self.timer = self.create_timer(
            0.1,
            self.main_order
        )

    def robot_pos_callback(self, msg):
        if self.last_robot_pos is None:
            self.get_logger().info(
                f"[MANUAL]: robot_position empfangen: x={msg.pos_x:.3f}, y={msg.pos_y:.3f}, z={msg.pos_z:.3f}"
            )
        self.last_robot_pos = msg
        self.last_robot_pos_time = time.time()
        self.waiting_for_robot_position = False

    def send_acceleration(self, acc_x, acc_y, acc_z):
        msg = RobotCmd()
        msg.accel_x = acc_x
        msg.accel_y = acc_y
        msg.accel_z = acc_z
        self.robot_cmd_pub.publish(msg)
        self.get_logger().debug(
            f"[MANUAL]: Publish robot_command: x={acc_x:.4f}, y={acc_y:.4f}, z={acc_z:.4f}"
        )

    def print_status_line(self):
        print(
            f"TARGET -> X: {self.target_x:.3f} | Y: {self.target_y:.3f} | Z: {self.target_z:.3f}",
            end="\r",
            flush=True,
        )

    def main_order(self):

        if self.waiting_for_robot_position:
            self.get_logger().info("[MANUAL]: Warte auf robot_position...")
            self.waiting_for_robot_position = False

        if self.main_state != self.last_state:
            self.get_logger().info(f"[MANUAL]: Zustand = {self.main_state.name}")
            self.last_state = self.main_state

        match self.main_state:

            case AxisControllerStates.EMPTY:
                self.ax_state_empty()

            case AxisControllerStates.INITIALIZING_AXIS_HW:
                self.ax_state_initializing_axis_hw()

            case AxisControllerStates.INITIALIZING_AXIS_SW:
                self.ax_state_initializing_axis_sw()

            case AxisControllerStates.RUNNING:
                self.ax_state_running()

        self.print_status_line()

    def ax_state_empty(self):

        if self.last_robot_pos is None:
            return

        self.get_logger().info("[MANUAL]: Starting Init")
        self.init_process.start()
        self.main_state = AxisControllerStates.INITIALIZING_AXIS_HW

    def ax_state_initializing_axis_hw(self):

        x_acc, y_acc, z_acc = self.init_process.robot_values(
            (
                self.last_robot_pos.pos_x,
                self.last_robot_pos.pos_y,
                self.last_robot_pos.pos_z
            )
        )

        self.send_acceleration(x_acc, y_acc, z_acc)

        if self.init_process.finished:
            self.main_state = AxisControllerStates.INITIALIZING_AXIS_SW

    def ax_state_initializing_axis_sw(self):

        planner_x = TrajectoryPlanner(
            MAX_VELOCITY_X,
            MAX_ACCELERATION_X,
            POSITION_TOLERANCE_X,
            VELOCITY_TOLERANCE_X
        )

        planner_y = TrajectoryPlanner(
            MAX_VELOCITY_Y,
            MAX_ACCELERATION_Y,
            POSITION_TOLERANCE_Y,
            VELOCITY_TOLERANCE_Y
        )

        planner_z = TrajectoryPlanner(
            MAX_VELOCITY_Z,
            MAX_ACCELERATION_Z,
            POSITION_TOLERANCE_Z,
            VELOCITY_TOLERANCE_Z
        )

        controller_x = Controller(
            KP_X,
            KD_X,
            MAX_ACCELERATION_X,
            TF_X
        )

        controller_y = Controller(
            KP_Y,
            KD_Y,
            MAX_ACCELERATION_Y,
            TF_Y
        )

        controller_z = Controller(
            KP_Z,
            KD_Z,
            MAX_ACCELERATION_Z,
            TF_Z
        )

        self.axis_x = Axis("X", controller_x, planner_x)
        self.axis_y = Axis("Y", controller_y, planner_y)
        self.axis_z = Axis("Z", controller_z, planner_z)

        self.offset_x = self.last_robot_pos.pos_x
        self.offset_y = self.last_robot_pos.pos_y
        self.offset_z = self.last_robot_pos.pos_z

        self.get_logger().info("[MANUAL]: Init Finished")
        self.get_logger().info(
            "[MANUAL]: Controls:\n"
            "W/S -> Y+\n"
            "A/D -> X+\n"
            "R/F -> Z+\n"
        )

        self.main_state = AxisControllerStates.RUNNING

    def ax_state_running(self):

        current_time = time.monotonic()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time

        self.axis_x.set_target(self.target_x * 0.8)
        self.axis_y.set_target(self.target_y * 0.8)
        self.axis_z.set_target(self.target_z)

        acc_x = self.axis_x.update(
            self.last_robot_pos.pos_x - self.offset_x,
            dt
        )

        acc_y = self.axis_y.update(
            self.last_robot_pos.pos_y - self.offset_y,
            dt
        )

        acc_z = self.axis_z.update(
            self.last_robot_pos.pos_z - self.offset_z,
            dt
        )

        self.send_acceleration(acc_x, acc_y, acc_z)

    def process_key(self, key: str):

        if key == 'w':
            self.target_y += STEP_SIZE
        elif key == 's':
            self.target_y -= STEP_SIZE
        elif key == 'd':
            self.target_x += STEP_SIZE
        elif key == 'a':
            self.target_x -= STEP_SIZE
        elif key == 'r':
            self.target_z += STEP_SIZE
        elif key == 'f':
            self.target_z -= STEP_SIZE

        elif key == 'W':
            self.target_y += FINE_STEP
        elif key == 'S':
            self.target_y -= FINE_STEP
        elif key == 'D':
            self.target_x += FINE_STEP
        elif key == 'A':
            self.target_x -= FINE_STEP
        elif key == 'R':
            self.target_z += FINE_STEP
        elif key == 'F':
            self.target_z -= FINE_STEP

        self.print_status_line()


def main(args=None):

    rclpy.init(args=args)

    node = ManualAxisController()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    executor = MultiThreadedExecutor()
    executor.add_node(node)

    print(
        "[MANUAL]: Controls:\n"
        "w/s -> Y+/- 0.01\n"
        "a/d -> X+/- 0.01\n"
        "r/f -> Z+/- 0.01\n"
        "W/S -> Y+/- 0.001\n"
        "A/D -> X+/- 0.001\n"
        "R/F -> Z+/- 0.001\n"
        "Ctrl+C -> Beenden\n"
    )

    try:
        tty.setcbreak(fd)

        while rclpy.ok():
            executor.spin_once(timeout_sec=0.01)

            rlist, _, _ = select.select([sys.stdin], [], [], 0.01)
            if rlist:
                key = sys.stdin.read(1)
                node.process_key(key)

    except (KeyboardInterrupt, ExternalShutdownException):
        pass

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()