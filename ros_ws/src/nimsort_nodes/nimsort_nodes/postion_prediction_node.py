import rclpy
from rclpy.node import Node, MutuallyExclusiveCallbackGroup
from nimsort_msgs.msg import NimSortPrediction, NimSortImageData
from rclpy.executors import ExternalShutdownException

class PositionPrediction(Node):
    def __init__(self):
        super().__init__('position_prediction_node')

        self.last_image_data = None
        
        self.image_data_sub = self.create_subscription(
            NimSortImageData,
            '/NimSortImageData',
            self.image_data_callback,
            10
        )
        self.prediction_pub = self.create_publisher(
            NimSortPrediction,
            '/NimSortPrediction',
            10
        )

        self.timer = self.create_timer(
            0.1,
            self.main_loop_callback
        )

    def image_data_callback(self, msg):
        self.last_image_data = msg

    def send_prediction(self, prediction): #TODO: add all fields
        msg = NimSortPrediction()
        #TODO fill msg
        self.prediction_pub.publish(msg)

    def main_loop_callback(self):
        pass

def main(args=None):
    rclpy.init(args=args)
    node = PositionPrediction()

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()