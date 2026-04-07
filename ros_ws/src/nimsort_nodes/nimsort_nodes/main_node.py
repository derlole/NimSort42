import rclpy
from rclpy.node import MutuallyExclusiveCallbackGroup, Node 
from nimsort_logic.nimsort_main.main_interface import MainInterface
from nimsort_logic.nimsort_main.main import NimSortMain 
from ro45_portalrobot_interfaces.msg import MotionState, Target, Prediction

class MainNode(Node):
    def __init__(self):
        super().__init__('main_node')
        
        self.nimsort_main = NimSortMain()
        self.publisher_ = self.create_publisher(Target, 'target', 10)
        
       
        self.callback_group = MutuallyExclusiveCallbackGroup()

        
        self.subscription_motion = self.create_subscription(
            MotionState,
            'motion_state',
            self.listener_callback_motion,
            10,
            callback_group=self.callback_group)
        
        self.subscription_prediction = self.create_subscription(
            Prediction,
            'prediction',
            self.listener_callback_prediction,
            10,
            callback_group=self.callback_group)

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
    
    from rclpy.executors import MultiThreadedExecutor
    
    main_node = MainNode()
    
    
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
    main() 