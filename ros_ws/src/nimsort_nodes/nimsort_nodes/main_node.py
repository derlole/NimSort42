import rclpy
from rclpy.node import MutuallyExclusiveCallbackGroup, Node 
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor

from nimsort_main.main import NimSortMain 
from nimsort_msgs.msg import NimSortPrediction, NimSortMotionState, NimSortTarget

class MainNode(Node):
    def __init__(self):
        super().__init__('nimsort_main_node')
        
        self.nimsort_main = NimSortMain()
        self.publisher_ = self.create_publisher(NimSortTarget, 'target', 10)
        
        self.subscription_motion = self.create_subscription(
            NimSortMotionState,
            'motion_state',
            self.listener_callback_motion,
            10)
        
        self.subscription_prediction = self.create_subscription(
            NimSortPrediction,
            'prediction',
            self.listener_callback_prediction,
            10)

    def listener_callback_motion(self, msg):
        """Verarbeitet MotionState Nachricht"""
        self.nimsort_main.process_motion_state(msg)
        self.get_logger().debug(f'MotionState verarbeitet. State: {self.nimsort_main.get_current_state()}')
    
    def listener_callback_prediction(self, msg):
        """Verarbeitet Prediction Nachricht und veröffentlicht Target"""
        target = self.nimsort_main.process_prediction(msg)
        
        if target is not None:
            self.publisher_.publish(target)
            self.get_logger().info(f'Target veröffentlicht. State: {self.nimsort_main.get_current_state()}')
        else:
            self.get_logger().debug(f'Keine Target für Prediction. State: {self.nimsort_main.get_current_state()}')

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