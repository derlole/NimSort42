import rclpy
from rclpy.node import Node 
import time
import threading
from nimsort_logic.nimsort_main.main_interface import MainInterface
from nimsort_logic.nimsort_main.main import NimSortMain 
from ro45_portalrobot_interfaces.msg import MotionState, Target, Prediction

class MainNode(Node):
    def __init__(self):
        super().__init__('main_node')
        
        self.nimsort_main = NimSortMain()
        self.publisher_ = self.create_publisher(Target, 'target', 10)
        self.callback_lock = threading.Lock()

        self.subscription_motion = self.create_subscription(
            MotionState,
            'motion_state',
            self.listener_callback_motion,
            10)
        
        self.subscription_prediction = self.create_subscription(
            Prediction,
            'prediction',
            self.listener_callback_prediction,
            10)

    def listener_callback_motion(self, msg):
        thread = threading.Thread(target=self._process_motion, args=(msg,))
        thread.start()
    
    def listener_callback_prediction(self, msg):
        thread = threading.Thread(target=self._process_prediction, args=(msg,))
        thread.start()
    
    def _process_motion(self, msg):
        with self.callback_lock:
            target_msg = self.nimsort_main.compute_target(msg)
            self.publisher_.publish(target_msg)
    
    def _process_prediction(self, msg):
        with self.callback_lock:
            target_msg = self.nimsort_main.compute_target(msg)
            self.publisher_.publish(target_msg)

def main(args=None):
    rclpy.init(args=args)
    
    from rclpy.executors import MultiThreadedExecutor
    
    main_node = MainNode()
    
    # MultiThreadedExecutor für parallele Callback-Verarbeitung
    executor = MultiThreadedExecutor()
    executor.add_node(main_node)
    
    try:
        executor.spin()
    except KeyboardInterrupt:
        main_node.get_logger().info('MainNode gestoppt')
        
    finally:
        executor.shutdown()
        rclpy.shutdown()


if __name__ == '__main__':
    main() s 