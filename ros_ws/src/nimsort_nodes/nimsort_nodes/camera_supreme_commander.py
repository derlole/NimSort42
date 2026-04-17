import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from tf2_ros import Buffer, TransformListener, LookupException, ConnectivityException, ExtrapolationException
from geometry_msgs.msg import PointStamped

from nimsort_msgs.msg import NimSortImageData

WORLD_FRAME = "world"
ROBOT_FRAME = "robot"
CAMERA_FRAME = "camera"

class Vision(Node):
    
    def __init__(self):
        super().__init__('camera_supreme_commander')

        self.publisher_ = self.create_publisher(
            NimSortImageData, 
            '/NimSortImageData', 
            10
        )
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        self.timer = self.create_timer(0.1, self.main_order)

    def tf_camera_to_world(self, x: float, y: float, z: float) -> PointStamped | None:
        """ transforms one point from camera-coordinatesystem into worl-coordinatesystem"""
        point = PointStamped()
        point.header.frame_id = CAMERA_FRAME
        point.header.stamp = self.get_clock().now().to_msg()

        point.point.x = x
        point.point.y = y
        point.point.z = z

        try:
            transformed = self.tf_buffer.transform(
                point,
                WORLD_FRAME,
                timeout=rclpy.duration.Duration(seconds=0.05)
            )
            return transformed
        
        except(LookupException, ConnectivityException, ExtrapolationException) as e:
            self.get_logger().warn(f"{str(e)}")
            return None

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