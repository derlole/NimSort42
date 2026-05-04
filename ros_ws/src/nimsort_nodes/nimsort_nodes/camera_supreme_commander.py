import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from tf2_ros import Buffer, TransformListener, LookupException, ConnectivityException, ExtrapolationException
import tf2_geometry_msgs
from geometry_msgs.msg import PointStamped, Point
import time

from nimsort_msgs.msg import NimSortImageData
from nimsort_vision.opencv_pipeline import OpencvPipeline


class Vision(Node):
    
    def __init__(self):
        super().__init__('camera_supreme_commander')

        self.image_data_publisher = self.create_publisher(
            NimSortImageData, 
            '/NimSortImageData', 
            10
        )
        self.timer = self.create_timer(0.1, self.main_order)

        self.pipeline = OpencvPipeline()
        
    def publish_image_data(self, x_wcs, y_wcs, z_wcs, ts, object_type, conveyor_belt_speed):
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
        print(f"[VN--][main_ord]: Starting main order{time.time()}")
        try:
            self.pipeline.captureImage()
            x_w, y_w, z_w, ts, image = self.pipeline.getImageData()

        except ValueError as e:
            self.get_logger.error("[VN--][main_ord]:" + str(e))

        # TODO insert trained_model_here to calculate the correct object_type


        self.publish_image_data(x_w, y_w, z_w, ts, 1, 0.01) # TODO repalce the consants at the time zou have them

def main(args=None):
    rclpy.init(args=args)
    node = Vision()

    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except (ExternalShutdownException, KeyboardInterrupt):
        node.get_logger().error("[VN--][main----]: Shutdown Node")

    finally:
        executor.shutdown()
        rclpy.shutdown()



if __name__ == '__main__':
    main()