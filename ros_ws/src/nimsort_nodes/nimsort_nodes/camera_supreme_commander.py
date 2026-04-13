import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor

from nimsort_msgs.msg import NimSortImageData



class Vision(Node):
    
    def __init__(self):
        super().__init__('camera_supreme_commander')

        self.publisher_ = self.create_publisher(
            NimSortImageData, 
            '/NimSortImageData', 
            10
        )
        
        self.timer = self.create_timer(0.1, self.main_order)

    def main_order(self):
        pass




def main(args=None):
    rclpy.init(args=args)
    node = Vision()

    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except (ExternalShutdownException, KeyboardInterrupt):
        node.get_logger().error("[ACN-][main----]: Shutdown Node")

    finally:
        executor.shutdown()
        rclpy.shutdown()



if __name__ == '__main__':
    main()