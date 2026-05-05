import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from nimsort_msgs.msg import NimSortPrediction, NimSortImageData
from geometry_msgs.msg import Point
from nimsort_vision.position_prediction_logic import PositionPrediction as PositionPredictionLogic

DEFAULT_CONVEYOR_BELT_SPEED = 0.01  # TODO: durch echte Messung ersetzen

class PositionPredictionNode(Node):
    def __init__(self):
        super().__init__('position_prediction_node')
        self.logic = PositionPredictionLogic()
        self.logic.set_conveyor_belt_speed(DEFAULT_CONVEYOR_BELT_SPEED)

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
        self.logic.set_object_data(
            object_type=msg.object_type,
            position=[
                msg.current_position_wcs.x,
                msg.current_position_wcs.y,
                msg.current_position_wcs.z,
            ],
            ts=msg.ts
        )
        self.logic.set_conveyor_belt_speed(msg.conveyor_belt_speed)

    def send_prediction(self, position: list[float], object_type: int):
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
            x, y, z, obj_type = self.logic.calculate_next_object_position()
            x2, y2, z2, obj_type2 = self.logic.calculate_second_object_position()
        except ValueError as e:
            self.get_logger().warn(str(e))
            return
        self.get_logger().debug(f"Objekt {obj_type} | XY: ({x:.3f}, {y:.3f})"
                                f"Objekt {obj_type2} | XY: ({x2:.3f}, {y2:.3f})")
        self.send_prediction([x, y, z], obj_type)
        self.send_prediction([x2, y2, z2], obj_type2)


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