import time
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from nimsort_motion.software_axis import SoftwareAxis
from nimsort_msgs.msg import NimSortMotionState, NimSortTarget, NimSortConveyorbeltSpeed
from nimsort_motion.axis_controller_states import AxisControllerStates
from nimsort_motion.init_process import InitProcess

from ro45_portalrobot_interfaces.msg import RobotCmd, RobotPos
from configs.config_axis import *

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

        self.axis = None
        self.last_target_time = time.time()
        self.last_robot_pos_time = time.time()
        self.last_update_time = time.monotonic()
        self.target_timeout_s = 1.0
        self.robot_pos_timeout_s = 0.5

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

    def send_acceleration(self, acc_x, acc_y, acc_z, gripper_active):
        msg = RobotCmd()
        msg.accel_x = acc_x
        msg.accel_y = acc_y
        msg.accel_z = acc_z
        msg.activate_gripper = gripper_active
        self.robot_cmd_pub.publish(msg)

    def nimsort_target_callback(self, msg):
        self.last_nimsort_target = msg
        self.last_target_time = time.time()
        self.get_logger().info(f"Received NimSortTarget: {msg}")

    def robot_pos_callback(self, msg):
        self.last_robot_pos = msg
        self.last_robot_pos_time = time.time()
        self.get_logger().info(f"Received RobotPos: {msg}")

    def publish_motion_state(self, reached, gripper_active):
        msg = NimSortMotionState()
        msg.reached = reached
        msg.gripper_active = gripper_active
        self.motion_state_pub.publish(msg)

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

            case AxisControllerStates.RETURNING_HOME:
                self.ax_state_returning_home()

            case AxisControllerStates.SHUTDOWN:
                self.ax_state_shutdown()
            

    def ax_state_empty(self):
        if self.last_nimsort_target is not None and self.init_process.should_start(self.last_nimsort_target.process_id):
            self.init_process.start()
            self.main_state = AxisControllerStates.INITIALIZING_AXIS_HW

    def ax_state_initializing_axis_hw(self):
        x_acc, y_acc, z_acc = self.init_process.robot_values((self.last_robot_pos.pos_x, self.last_robot_pos.pos_y, self.last_robot_pos.pos_z))
        if self.init_process.finished:
            self.main_state = AxisControllerStates.INITIALIZING_AXIS_SW
        self.send_acceleration(x_acc, y_acc, z_acc, False)


    def ax_state_initializing_axis_sw(self):
        self.axis = SoftwareAxis()

        self.axis.set_offset(self.last_robot_pos.pos_x, self.last_robot_pos.pos_y, self.last_robot_pos.pos_z)
        
        self.get_logger().info(f"[ACN-][ax_in_sw]: X Axis: {self.axis.axis_x}")
        self.get_logger().info(f"[ACN-][ax_in_sw]: Y Axis: {self.axis.axis_y}")
        self.get_logger().info(f"[ACN-][ax_in_sw]: Z Axis: {self.axis.axis_z}")

        self.main_state = AxisControllerStates.RUNNING

    def ax_state_running(self):
        current_time = time.monotonic()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        currently_reached = self.axis.reached(self.last_nimsort_target.process_id)

        if self.last_nimsort_target is None:
            self.get_logger().warn("[ACN-][ax_run]: No target received yet")
            self.main_state = AxisControllerStates.RETURNING_HOME
            return
        
        print(f"[ACN-][ax_run]: Last Robot Pos: {self.axis.axis_x.target_reached}, {self.axis.axis_y.target_reached}, {self.axis.axis_z.target_reached}")
        
        if (time.time() - self.last_target_time > self.target_timeout_s) or (time.time() - self.last_robot_pos_time > self.robot_pos_timeout_s):
            self.get_logger().warn("[ACN-][ax_run]: Target oder robot_pos timeout -> returning home")

            self.init_process.reset()
            self.init_process.start(accel = (RESCUE_ACCELERATION_X, RESCUE_ACCELERATION_Y, RESCUE_ACCELERATION_Z))
            self.main_state = AxisControllerStates.RETURNING_HOME
            return
        
        self.axis.set_target(self.last_nimsort_target.target_point.x, self.last_nimsort_target.target_point.y, self.last_nimsort_target.target_point.z)
        acc_x, acc_y, acc_z = self.axis.update(self.last_robot_pos.pos_x, self.last_robot_pos.pos_y, self.last_robot_pos.pos_z, dt)
        gripper_should = self.axis.gripper_active(self.last_nimsort_target.process_id)

        # if currently_reached and self.last_nimsort_target is not None: # TODO how the old impl worked wtf
        #     self.publish_motion_state(True, gripper_should)

        self.publish_motion_state(currently_reached, gripper_should)
        self.send_acceleration(acc_x, acc_y, acc_z, gripper_should)

    def ax_state_returning_home(self):
        x_acc, y_acc, z_acc = self.init_process.robot_values((self.last_robot_pos.pos_x, self.last_robot_pos.pos_y, self.last_robot_pos.pos_z))

        self.send_acceleration(x_acc, y_acc, z_acc, False)

        if self.init_process.finished:
            self.main_state = AxisControllerStates.SHUTDOWN

    def ax_state_shutdown(self):
        raise RuntimeError("[ACN-][shutdown]: Destroying node")

def main(args=None):
    rclpy.init(args=args)
    node = AxisController()

    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except (ExternalShutdownException, KeyboardInterrupt):
        node.get_logger().error("[ACN-][main----]: Shutdown Node")
    
    except RuntimeError as e:
        node.get_logger().error(f"[ACN-][main----]: {str(e)}")

    finally:
        executor.shutdown()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

