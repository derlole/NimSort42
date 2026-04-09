import rclpy
from rclpy.node import Node
from sensor_msgs.msg import String
from rclpy.executors import ExternalShutdownException


class Vision(Node):
    
    def __init__(self):
        super().__init__('camera_supreme_commander')

        self.publisher_ = self.create_publisher(
            String, 
            'output_topic', 
            10
        )
        
        self.timer = self.create_timer(0.1, self.main_order)

    def main_order(self):
        pass




def main(args=None):
    rclpy.init(args=args)
    node = Vision()

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()