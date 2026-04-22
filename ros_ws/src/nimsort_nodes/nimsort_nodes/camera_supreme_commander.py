import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from tf2_ros import Buffer, TransformListener, LookupException, ConnectivityException, ExtrapolationException
import tf2_geometry_msgs
from geometry_msgs.msg import PointStamped, Point
import time

from nimsort_msgs.msg import NimSortImageData
from nimsort_vision.opencv_pipeline import OpencvPipeline

WORLD_FRAME = "world"
ROBOT_FRAME = "robot"
CAMERA_FRAME = "camera"

class Vision(Node):
    
    def __init__(self):
        super().__init__('camera_supreme_commander')

        self.image_data_publisher = self.create_publisher(
            NimSortImageData, 
            '/NimSortImageData', 
            10
        )
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.timer = self.create_timer(0.1, self.main_order)

        self.pipeline = OpencvPipeline()

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
                timeout = rclpy.duration.Duration(seconds = 0.05)
            )
            return transformed
        
        except(LookupException, ConnectivityException, ExtrapolationException) as e:
            self.get_logger().warn(f"{str(e)}")
            return None
        
    def publish_image_data(self, x_wcs: float, y_wcs: float, z_wcs: float, ts: int, object_type: int, conveyor_belt_speed: float):
        msg = NimSortImageData()
        msg.current_position_wcs = Point()

        msg.current_position_wcs.x = x_wcs
        msg.current_position_wcs.y = y_wcs
        msg.current_position_wcs.z = z_wcs
        msg.object_type = object_type
        msg.ts = ts
        msg.conveyor_belt_speed = conveyor_belt_speed 

        self.image_data_publisher.publish(msg)


    def main_order(self):
        print(f"[ACN-][main_ord]: Starting main order{time.time()}")
        try:
            self.pipeline.captureImage()
            x_ccs, y_ccs, z_ccs, ts, image = self.pipeline.getImageData()

        except ValueError as e:
            self.get_logger.error("[ACN-][main_ord]:" + str(e))

        # TODO insert trained_model_here to calculate the correct object_type
        point_wcs = self.tf_camera_to_world(x_ccs, y_ccs, z_ccs)

        self.publish_image_data(point_wcs.point.x, point_wcs.point.y, point_wcs.point.z, ts, 1, 0.01) # TODO repalce the consants at the time zou have them

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