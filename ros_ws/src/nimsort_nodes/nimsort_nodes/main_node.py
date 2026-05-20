import time
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from geometry_msgs.msg import Point
from std_msgs.msg import Bool
from nimsort_main.main_logic import NimSortMain
from nimsort_msgs.msg import NimSortPrediction, NimSortMotionState, NimSortTarget

class MainNode(Node):
    def __init__(self):
        super().__init__('nimsort_main_node')
        self.nimsort_main = NimSortMain()

        self.target_publisher = self.create_publisher(NimSortTarget, '/NimSortTarget', 10)
        self.feedback_publisher = self.create_publisher(Bool, '/NimSortPredictionFeedback', 10)

        self.subscription_motion = self.create_subscription(
            NimSortMotionState,
            '/NimSortMotionState',
            self.listener_callback_motion,
            10)

        self.subscription_prediction = self.create_subscription(
            NimSortPrediction,
            '/NimSortPrediction',
            self.listener_callback_prediction,
            10)

        self.timer = self.create_timer(0.1, self.main_order)
        self.last_prediction_time = time.time()

    def listener_callback_motion(self, msg):
        """Verarbeitet MotionState Nachricht."""
        self.nimsort_main.set_motion_state(msg.reached, msg.gripper_active)

    def listener_callback_prediction(self, msg: NimSortPrediction):
        """
        Verarbeitet Prediction und sendet sofort Feedback zurück.
        
        False = MainNode akzeptiert das Objekt (kann noch gegriffen werden)
        True  = MainNode lehnt ab (bereits gegriffen oder ungültig)
        """
        self.last_prediction_time = time.time()

        if msg.object_type == -1:
            self._publish_feedback(rejected=True)
            return

        accepted = self.nimsort_main.set_target_to_pick(
            x=msg.predicted_position_wcs.x,
            y=msg.predicted_position_wcs.y,
            z=msg.predicted_position_wcs.z,
            object_type=msg.object_type
        )

        # False = akzeptiert (noch greifbar), True = abgelehnt (nicht greifbar)
        self._publish_feedback(rejected=not accepted)

    def _publish_feedback(self, rejected: bool):
        """
        Publiziert Feedback an PositionPrediction.
        False = Objekt akzeptiert / greifbar
        True  = Objekt abgelehnt / nicht mehr relevant
        """
        msg = Bool()
        msg.data = rejected
        self.feedback_publisher.publish(msg)
        self.get_logger().debug(f'[MAIN][feedback]: rejected={rejected}')

    def publish_target(self, x, y, z, process_id):
        process_id = process_id.value
        msg = NimSortTarget()
        msg.target_point = Point(x=x, y=y, z=z)
        msg.process_id = process_id
        self.target_publisher.publish(msg)

    def main_order(self):
        """State Machine Logik."""
        if time.time() - self.last_prediction_time > 1.0:
            self.get_logger().warning("[MAIN][main_ord]: Keine aktuellen Predictions.")
            raise RuntimeError("Keine aktuellen Predictions.")

        x, y, z, process_id = self.nimsort_main.state_machine()
        self.publish_target(x, y, z, process_id)
        self.get_logger().debug(f'[MAIN][main_ord]: Published Target - X: {x:.3f}, Y: {y:.3f}, Z: {z:.3f}, ProcessID: {process_id}')
        self.get_logger().debug(f'[MAIN][main_ord]: Current State: {self.nimsort_main.get_current_state().name}')


def main(args=None):
    rclpy.init(args=args)
    main_node = MainNode()
    executor = MultiThreadedExecutor()
    executor.add_node(main_node)
    try:
        executor.spin()
    except (ExternalShutdownException, KeyboardInterrupt):
        main_node.get_logger().error("[MAIN][main----]: Shutdown Node")
    except RuntimeError as e:
        main_node.get_logger().error(f"[MAIN][main----]: {str(e)}")
    finally:
        executor.shutdown()
        rclpy.shutdown()

if __name__ == '__main__':
    main()