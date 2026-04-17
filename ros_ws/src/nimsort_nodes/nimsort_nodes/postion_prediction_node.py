import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from nimsort_msgs.msg import NimSortPrediction, NimSortImageData
from geometry_msgs.msg import Point
from nimsort_vision.position_prediction_logic import PositionPrediction as PositionPredictionLogic

class PositionPredictionNode(Node):

    def __init__(self):
        super().__init__('position_prediction_node')
        self.logic = PositionPredictionLogic()
        self.object_id_counter = 0

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
        self.timer = self.create_timer(0.1, self.main_order)

    def image_data_callback(self, msg: NimSortImageData):
        self.logic.set_conveyor_belt_speed(msg.conveyor_belt_speed)
        object_id = self.object_id_counter
        self.object_id_counter += 1
        self.logic.set_object_data(
            object_id=object_id,
            object_type=msg.object_type,
            position=(
                msg.current_position_wcs.x,
                msg.current_position_wcs.y,
                msg.current_position_wcs.z,
            ),
            ts=msg.ts,
            speed=getattr(msg, 'speed', 1.0),
        )

    def send_prediction(self, position: tuple[float, float, float], object_type: int):
        msg = NimSortPrediction()
        msg.predicted_position_wcs = Point(
            x=position[0],
            y=position[1],
            z=position[2],
        )
        msg.object_type = object_type
        self.prediction_pub.publish(msg)

    def main_order(self):
        try:
            magic_obj = self.logic.get_next_object_to_publish()
        except ValueError as e:
            self.get_logger().warn(str(e))
            return

        self.get_logger().debug(f"Objekt {magic_obj.object_type} | XY: ({magic_obj.position[0]:.3f}, {magic_obj.position[1]:.3f})")
        self.send_prediction(magic_obj.position, magic_obj.object_type)


def main(args=None):
    rclpy.init(args=args)
    node = PositionPredictionNode()
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