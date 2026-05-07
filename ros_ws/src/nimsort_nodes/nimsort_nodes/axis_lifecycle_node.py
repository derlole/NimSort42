import time

import rclpy
from rclpy.lifecycle import LifecycleNode
from rclpy.lifecycle import TransitionCallbackReturn
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor

from nimsort_motion.axis import Axis
from nimsort_motion.controller import Controller
from nimsort_motion.trajectroy_planner import TrajectoryPlanner
from nimsort_msgs.msg import NimSortMotionState, NimSortTarget, NimSortConveyorbeltSpeed
from nimsort_motion.axis_controller_states import AxisControllerStates
from nimsort_motion.init_process import InitProcess
from ro45_portalrobot_interfaces.msg import RobotCmd, RobotPos

MAX_VELOCITY_X = 0.05
MAX_VELOCITY_Y = 0.05
MAX_VELOCITY_Z = 0.05
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
D_FILTER_ALPHA_X = 0.5
D_FILTER_ALPHA_Y = 0.5
D_FILTER_ALPHA_Z = 0.5
TF_X = 0.00875
TF_Y = 0.00875
TF_Z = 0.00875


class AxisControllerLifecycleNode(LifecycleNode):
    def __init__(self):
        super().__init__('nimsort_axis_controller_lifecycle_node')

        self.last_robot_pos = None
        self.last_nimsort_target = None
        self.last_conveyorbelt_speed = None
        self.main_state = AxisControllerStates.EMPTY
        self.init_process = InitProcess()
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.offset_z = 0.0

        self.axis_x = None
        self.axis_y = None
        self.axis_z = None

        self.nimsort_target_sub = None
        self.nimsort_conveyorbelt_speed_sub = None
        self.robot_pos_sub = None
        self.motion_state_pub = None
        self.robot_cmd_pub = None
        self.timer = None
        self.timer_period = 0.1

    def send_acceleration(self, acc_x, acc_y, acc_z):
        msg = RobotCmd()
        msg.accel_x = acc_x
        msg.accel_y = acc_y
        msg.accel_z = acc_z
        self.robot_cmd_pub.publish(msg)

    def main_order(self):
        match self.main_state:
            case AxisControllerStates.EMPTY:
                self.get_logger().info('State: EMPTY')
                self.ax_state_empty()

            case AxisControllerStates.INITIALIZING_AXIS_HW:
                self.get_logger().info('State: INITIALIZING_AXIS_HW')
                self.ax_state_initializing_axis_hw()

            case AxisControllerStates.INITIALIZING_AXIS_SW:
                self.ax_state_initializing_axis_sw()

            case AxisControllerStates.RUNNING:
                self.ax_state_running()

    def nimsort_target_callback(self, msg):
        self.last_nimsort_target = msg
        self.get_logger().info(f'Received NimSortTarget: {msg}')

    def nimsort_conveyorbelt_speed_callback(self, msg):
        self.last_conveyorbelt_speed = msg.conveyorbelt_speed

    def robot_pos_callback(self, msg):
        self.last_robot_pos = msg
        self.get_logger().info(f'Received RobotPos: {msg}')

    def ax_state_empty(self):
        if self.last_nimsort_target is not None and self.last_nimsort_target.process_id == 1:
            self.init_process.start()
            self.main_state = AxisControllerStates.INITIALIZING_AXIS_HW

    def ax_state_initializing_axis_hw(self):
        if self.last_robot_pos is None:
            self.get_logger().warning('No robot position available during HW initialization')
            return

        x_acc, y_acc, z_acc = self.init_process.robot_values(
            (self.last_robot_pos.pos_x, self.last_robot_pos.pos_y, self.last_robot_pos.pos_z)
        )
        if self.init_process.finished:
            self.main_state = AxisControllerStates.INITIALIZING_AXIS_SW
        self.send_acceleration(x_acc, y_acc, z_acc)

    def ax_state_initializing_axis_sw(self):
        trajectrory_planner_x = TrajectoryPlanner(
            MAX_VELOCITY_X,
            MAX_ACCELERATION_X,
            POSITION_TOLERANCE_X,
            VELOCITY_TOLERANCE_X,
        )
        trajectrory_planner_y = TrajectoryPlanner(
            MAX_VELOCITY_Y,
            MAX_ACCELERATION_Y,
            POSITION_TOLERANCE_Y,
            VELOCITY_TOLERANCE_Y,
        )
        trajectrory_planner_z = TrajectoryPlanner(
            MAX_VELOCITY_Z,
            MAX_ACCELERATION_Z,
            POSITION_TOLERANCE_Z,
            VELOCITY_TOLERANCE_Z,
        )

        controller_x = Controller(KP_X, KD_X, MAX_ACCELERATION_X, TF_X)
        controller_y = Controller(KP_Y, KD_Y, MAX_ACCELERATION_Y, TF_Y)
        controller_z = Controller(KP_Z, KD_Z, MAX_ACCELERATION_Z, TF_Z)

        self.axis_x = Axis('X', controller_x, trajectrory_planner_x)
        self.axis_y = Axis('Y', controller_y, trajectrory_planner_y)
        self.axis_z = Axis('Z', controller_z, trajectrory_planner_z)

        self.offset_x = self.last_robot_pos.pos_x
        self.offset_y = self.last_robot_pos.pos_y
        self.offset_z = self.last_robot_pos.pos_z

        self.get_logger().info(f'[ACN-][ax_in_sw]: X Axis: {self.axis_x}')
        self.get_logger().info(f'[ACN-][ax_in_sw]: Y Axis: {self.axis_y}')
        self.get_logger().info(f'[ACN-][ax_in_sw]: Z Axis: {self.axis_z}')

        self.main_state = AxisControllerStates.RUNNING

    def publish_motion_state(self, reached, gripper_active):
        msg = NimSortMotionState()
        msg.reached = reached
        msg.gripper_active = gripper_active
        self.motion_state_pub.publish(msg)

    def ax_state_running(self):
        if self.axis_x is None or self.axis_y is None or self.axis_z is None:
            self.get_logger().warning('Axis controllers are not initialized while entering RUNNING state')
            return

        if self.last_nimsort_target is None or self.last_robot_pos is None:
            self.get_logger().warning('Missing target or robot position during RUNNING state')
            return

        self.get_logger().debug(
            f'[ACN-][ax_run]: Last Robot Pos: {self.axis_x.target_reached}, '
            f'{self.axis_y.target_reached}, {self.axis_z.target_reached}'
        )

        if self.axis_x.target_reached and self.axis_y.target_reached and self.axis_z.target_reached:
            self.publish_motion_state(True, False)

        self.axis_x.set_target(self.last_nimsort_target.target_point.x * 0.8)
        self.axis_y.set_target(self.last_nimsort_target.target_point.y * 0.8)
        self.axis_z.set_target(self.last_nimsort_target.target_point.z * 0.8)

        acc_x = self.axis_x.update(self.last_robot_pos.pos_x - self.offset_x, 0.1)
        acc_y = self.axis_y.update(self.last_robot_pos.pos_y - self.offset_y, 0.1)
        acc_z = self.axis_z.update(self.last_robot_pos.pos_z - self.offset_z, 0.1)

        self.send_acceleration(acc_x, acc_y, acc_z)

    def on_configure(self, state):
        self.get_logger().info('Configuring lifecycle node')

        self.nimsort_target_sub = self.create_subscription(
            NimSortTarget,
            '/NimSortTarget',
            self.nimsort_target_callback,
            10,
        )
        self.nimsort_conveyorbelt_speed_sub = self.create_subscription(
            NimSortConveyorbeltSpeed,
            '/NimSortConveyorbeltSpeed',
            self.nimsort_conveyorbelt_speed_callback,
            10,
        )
        self.robot_pos_sub = self.create_subscription(
            RobotPos,
            'robot_position',
            self.robot_pos_callback,
            10,
        )

        self.motion_state_pub = self.create_publisher(
            NimSortMotionState,
            '/NimSortMotionState',
            10,
        )
        self.robot_cmd_pub = self.create_publisher(
            RobotCmd,
            'robot_command',
            10,
        )

        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state):
        self.get_logger().info('Activating lifecycle node')
        if self.motion_state_pub is not None:
            self.motion_state_pub.on_activate()
        if self.robot_cmd_pub is not None:
            self.robot_cmd_pub.on_activate()

        self.timer = self.create_timer(self.timer_period, self.main_order)
        return TransitionCallbackReturn.SUCCESS

    def on_deactivate(self, state):
        self.get_logger().info('Deactivating lifecycle node')
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None

        if self.motion_state_pub is not None:
            self.motion_state_pub.on_deactivate()
        if self.robot_cmd_pub is not None:
            self.robot_cmd_pub.on_deactivate()

        return TransitionCallbackReturn.SUCCESS

    def on_cleanup(self, state):
        self.get_logger().info('Cleaning up lifecycle node')
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None

        self.nimsort_target_sub = None
        self.nimsort_conveyorbelt_speed_sub = None
        self.robot_pos_sub = None
        self.motion_state_pub = None
        self.robot_cmd_pub = None
        return TransitionCallbackReturn.SUCCESS

    def drive_home_before_shutdown(self):
        self.get_logger().info('[ACN-][shutdown]: Fahre zum Grundposition mit kurzer Beschleunigung')
        if self.robot_cmd_pub is None:
            self.get_logger().warning('[ACN-][shutdown]: Kein robot_cmd_pub vorhanden, beschleunigung nicht gesendet')
            return

        home_acc = (0.005, 0.005, -0.01)
        self.send_acceleration(*home_acc)
        time.sleep(1.0)
        self.get_logger().info('[ACN-][shutdown]: Sende Stopp-Beschleunigung')
        self.send_acceleration(0.0, 0.0, 0.0)

    def on_shutdown(self, state):
        self.get_logger().info('Shutting down lifecycle node')
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None

        self.drive_home_before_shutdown()
        return TransitionCallbackReturn.SUCCESS


def main(args=None):
    rclpy.init(args=args)
    node = AxisControllerLifecycleNode()

    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except (ExternalShutdownException, KeyboardInterrupt):
        node.get_logger().error('[ACN-][main----]: Shutdown Lifecycle Node')
    finally:
        executor.shutdown()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
