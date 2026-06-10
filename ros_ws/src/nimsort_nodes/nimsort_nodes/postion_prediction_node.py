import time
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from nimsort_msgs.msg import NimSortPrediction, NimSortImageData, NimSortConveyorbeltSpeed
from geometry_msgs.msg import Point
from std_msgs.msg import Bool
from nimsort_vision.position_prediction_logic import PositionPrediction as PositionPredictionLogic


from configs.config_position_prediction import DEFAULT_CONVEYOR_BELT_SPEED, SENTINEL_MSG

class PositionPredictionNode(Node):

    def __init__(self):
        super().__init__('position_prediction_node')
        self.logic = PositionPredictionLogic()
        self.logic.set_conveyorbelt_speed(DEFAULT_CONVEYOR_BELT_SPEED)

        self.image_data_sub = self.create_subscription(
            NimSortImageData,
            '/NimSortImageData',
            self.image_data_callback,
            10
        )
        self.conveyorbelt_speed_sub = self.create_subscription(
            NimSortConveyorbeltSpeed,
            '/NimSortConveyorbeltSpeed',
            self.conveyorbelt_speed_callback,
            10
        )
        self.prediction_feedback_sub = self.create_subscription(
            Bool,
            '/NimSortPredictionFeedback',
            self.prediction_feedback_callback,
            10
        )
        self.prediction_pub = self.create_publisher(
            NimSortPrediction,
            '/NimSortPrediction',
            10
        )
        self.timer = self.create_timer(0.1, self.main_order)
        self.last_image_data_time = time.time()

    def image_data_callback(self, msg: NimSortImageData):
        self.last_image_data_time = time.time()
        if msg.current_position_wcs.x == -1.0:
            return

        self.logic.set_object_data(
            object_type=msg.object_type,
            position=[
                msg.current_position_wcs.x,
                msg.current_position_wcs.y,
                msg.current_position_wcs.z,
            ],
            ts=msg.ts
        )

    def conveyorbelt_speed_callback(self, msg: NimSortConveyorbeltSpeed):
        self.logic.set_conveyorbelt_speed(msg.conveyorbelt_speed)

    def prediction_feedback_callback(self, msg: Bool):
        if not msg.data:
            self.logic.remove_first_object()
            self.main_order()

    def send_prediction(self, position: tuple[float, float, float, int]) -> None:
        x, y, z, obj_type = position
        msg = NimSortPrediction()
        msg.predicted_position_wcs = Point(x=x, y=y, z=z)
        msg.object_type = obj_type
        self.prediction_pub.publish(msg)

    def main_order(self):
        if time.time() - self.last_image_data_time > 1.0:
            self.get_logger().warning("[PoPr][main_ord]: Keine aktuellen ImageData, Killing myself.")
            raise RuntimeError("Keine aktuellen ImageData, State Killing myself.")
        
        try:
            next_object = self.logic.calculate_next_object_positions()[0]
        except ValueError as e:
            self.get_logger().warn(str(e))
            next_object = SENTINEL_MSG

        self.get_logger().debug(
            f"Objekt {next_object[3]}  | XY: ({next_object[0]:.3f}, {next_object[1]:.3f})\n"
        )
        self.send_prediction(next_object)


def main(args=None):
    rclpy.init(args=args)
    node = PositionPredictionNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    
    try:
        executor.spin()
    except (ExternalShutdownException, KeyboardInterrupt):
        node.get_logger().error("[PoPr][main----]: Shutdown Node")

    except RuntimeError as e:
        node.get_logger().error(f"[PoPr][main----]: {str(e)}")

    finally:
        executor.shutdown()
        rclpy.shutdown()


if __name__ == '__main__':
    main()