import time
import rclpy
from rclpy.node import MutuallyExclusiveCallbackGroup, Node 
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from geometry_msgs.msg import Point
from std_msgs.msg import Bool
from nimsort_main.main_logic import NimSortMain 
from nimsort_vision.magic_object import MagicObject
from nimsort_msgs.msg import NimSortPrediction, NimSortMotionState, NimSortTarget

class MainNode(Node):
    def __init__(self):
        super().__init__('nimsort_main_node')
        
        self.nimsort_main = NimSortMain()
        self.publisher= self.create_publisher(NimSortTarget, '/NimSortTarget', 10)
        self.prediction_feedback_pub = self.create_publisher(Bool, '/NimSortPredictionFeedback', 10)
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
        """Verarbeitet MotionState Nachricht"""
        self.nimsort_main.set_motion_state(msg.reached, msg.gripper_active)
       
    
    def listener_callback_prediction(self, msg):
        """handles incoming predictions and sends feedback to the prediction node"""
        self.last_prediction_time = time.time()
        if msg.object_type == -1:
            return
        
        prediction_feedback = self.nimsort_main.set_target_to_pick(x=msg.predicted_position_wcs.x, y=msg.predicted_position_wcs.y, z=msg.predicted_position_wcs.z, object_type=msg.object_type)
        self.publish_prediction_feedback(prediction_feedback)
    
    def publish_prediction_feedback(self, prediction_feedback: bool) -> None:
        """Publishes feedback on the reveived prediction to the prediction node, so it can decide whether to keep or remove the prediction"""
        msg = Bool()
        msg.data = prediction_feedback
        self.prediction_feedback_pub.publish(msg)

    def publish_target(self, x, y, z, process_id):
        process_id = process_id.value 
        msg=NimSortTarget()
        msg.target_point=Point(
            x=x,
            y=y,
            z=z 
        )
        msg.process_id=process_id
        self.publisher.publish(msg)

    def main_order(self):
        """State Machine Logik, die basierend auf aktuellen Zuständen entscheidet."""
        if time.time() - self.last_prediction_time > 1.0:
            self.get_logger().warning("[MAIN][main_ord]: Keine aktuellen Predictions, Killing myself.")
            raise RuntimeError("Keine aktuellen Predictions, State Killing myself.")

        x, y, z, process_id = self.nimsort_main.state_machine()
        self.publish_target(x, y, z, process_id)
    
        
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