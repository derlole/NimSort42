import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from tf2_ros import Buffer, TransformListener, LookupException, ConnectivityException, ExtrapolationException
import tf2_geometry_msgs
from geometry_msgs.msg import PointStamped, Point
import time

from nimsort_msgs.msg import NimSortImageData, NimSortConveyorbeltSpeed
from nimsort_vision.opencv_pipeline import OpencvPipeline
from nimsort_vision.conveyor_speed import ConveyorSpeedEstimator


class Vision(Node):
    
    def __init__(self):
        super().__init__('camera_supreme_commander')

        self.image_data_publisher = self.create_publisher(
            NimSortImageData, 
            '/NimSortImageData', 
            10
        )
        self.conveyorbelt_speed_publisher = self.create_publisher(
            NimSortConveyorbeltSpeed,
            '/NimSortConveyorbeltSpeed',
            10
        )
        self.timer = self.create_timer(0.1, self.main_order)

        try:
            self.pipeline = OpencvPipeline()
        except RuntimeError as e:
            self.get_logger().error("[VN--][__init__]:" + str(e))
            raise

        try:
            self.speed = ConveyorSpeedEstimator()
        except RuntimeError as e:
            self.get_logger().error("[VN--][__init__]:" + str(e))
            raise


    def publish_image_data(self, x_wcs, y_wcs, z_wcs, ts, object_type):
        msg = NimSortImageData()
        msg.current_position_wcs = Point()

        msg.current_position_wcs.x = x_wcs
        msg.current_position_wcs.y = y_wcs
        msg.current_position_wcs.z = z_wcs
        msg.object_type = object_type
        msg.ts = ts
        
        self.image_data_publisher.publish(msg)


    def publish_conveyorbelt_speed(self, conveyorbelt_speed):
        msg = NimSortConveyorbeltSpeed()
        msg.conveyorbelt_speed = conveyorbelt_speed 

        self.conveyorbelt_speed_publisher.publish(msg)


    def main_order(self):
        print(f"[VN--][main_ord]: Starting main order{time.time()}")

        objects = []
        try:
            self.pipeline.captureImage()
            objects, ts, image = self.pipeline.getImageData()

        except RuntimeError as e:
            self.get_logger().error("[VN--][main_ord]:" + str(e))

        except ValueError as e:
            self.publish_image_data(-1.0, -1.0, -1.0, -1, -1) # publish dummy data to indicate error / no objects found


        try:
            speed = self.speed.update(objects[0][0], ts)

        except RuntimeError as e:
            self.get_logger().error("[VN--][main_ord]:" + str(e))

            
        # TODO insert trained_model_here to calculate the correct object_type


        for x_w, y_w, z_w in objects:
            self.publish_image_data(x_w, y_w, z_w, ts, 1) # TODO repalce the consants at the time you have the real object type
            
        self.publish_conveyorbelt_speed(speed) # TODO replace the constant at the time you have the real speed

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