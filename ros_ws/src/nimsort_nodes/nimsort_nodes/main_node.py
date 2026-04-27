import rclpy
from rclpy.node import MutuallyExclusiveCallbackGroup, Node 
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from geometry_msgs.msg import Point
from nimsort_main.main import NimSortMain 
from nimsort_msgs.msg import NimSortPrediction, NimSortMotionState, NimSortTarget

class MainNode(Node):
    def __init__(self):
        super().__init__('nimsort_main_node')
        
        self.nimsort_main = NimSortMain()
        self.publisher= self.create_publisher(NimSortTarget, 'target', 10)
        
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

    def listener_callback_motion(self, msg):
        """Verarbeitet MotionState Nachricht"""
        self.nimsort_main.set_motion_state(msg.reached,msg.gripper_active)
       
    
    def listener_callback_prediction(self, msg):
        """Verarbeitet Prediction Nachricht und veröffentlicht Target"""
        self.get_logger().info(f'Prediction empfangen. X: {msg.predicted_position_wcs.x:.2f}, Y: {msg.predicted_position_wcs.y:.2f}, Z: {msg.predicted_position_wcs.z:.2f}, Objekt-Typ: {msg.object_type}')
        target = self.nimsort_main.process_prediction(msg)
        
        if target is not None:
            self.publisher_.publish(target)
            self.get_logger().info(f'Target veröffentlicht. State: {self.nimsort_main.get_current_state()}')
        else:
            self.get_logger().debug(f'Keine Target für Prediction. State: {self.nimsort_main.get_current_state()}')

    def publish_target(self, x, y, z, process_id):
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
        
    finally:
        executor.shutdown()
        rclpy.shutdown()


if __name__ == '__main__':
    main() 