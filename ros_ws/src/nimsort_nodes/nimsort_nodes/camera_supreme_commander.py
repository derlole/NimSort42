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
from nimsort_vision.feature_detection import FeatureDetection


class Vision(Node):
    
    def __init__(self):
        super().__init__('camera_supreme_commander')

        self.declare_parameter('camera_index', 4)
        self.camera_index = self.get_parameter('camera_index').get_parameter_value().integer_value
        self.last_speed = None

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
            self.pipeline = OpencvPipeline(self.camera_index)
        except RuntimeError as e:
            self.get_logger().error("[VN--][__init__]:" + str(e))
            raise

        try:
            self.speed_calc = ConveyorSpeedEstimator()
        except RuntimeError as e:
            self.get_logger().error("[VN--][__init__]:" + str(e))
            raise
        
        try:
            self.feature_detector = FeatureDetection()
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


        speed = None
        try:
            if len(objects) > 0:
                speed = self.speed_calc.update(objects[0][0], ts)
                if speed is not None and speed > 0.0:
                    self.last_speed = speed
                else:
                    speed = self.last_speed
                    
                self.get_logger().info(f"[VN--][main_ord]: Estimated speed: {speed} m/s")

        except RuntimeError as e:
            self.get_logger().error("[VN--][main_ord]:" + str(e))


        try:
            feature = self.feature_detector.getFeature(image)
        
        except RuntimeError as e:
            self.get_logger().error("[VN--][main_ord]:" + str(e))

        for x_w, y_w, z_w in objects:
            self.publish_image_data(x_w, y_w, z_w, ts, 1) # TODO repalce the consants at the time you have the real object type
            
        if speed is None:
            speed = 0.01
        self.publish_conveyorbelt_speed(speed)


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