import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from nimsort_msgs.msg import NimSortPrediction, NimSortImageData
from geometry_msgs.msg import Point
from nimsort_vision.position_prediction_logic import PositionPrediction as PositionPredictionLogic

DEFAULT_CONVEYOR_BELT_SPEED = 0.01  # TODO: durch echte Messung ersetzen
SENTINEL = (-1.0, -1.0, -1.0, -1)


class PositionPredictionNode(Node):

    def __init__(self):
        super().__init__('position_prediction_node')
        self.logic = PositionPredictionLogic()
        self.logic.set_conveyor_belt_speed(DEFAULT_CONVEYOR_BELT_SPEED)
        self.bool_no_objects_logged = False

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
        if msg.current_position_wcs.x == -1 and msg.current_position_wcs.y == -1 and msg.current_position_wcs.z == -1:
            self.bool_no_objects_logged = True
            return
        elif self.bool_no_objects_logged:
            self.get_logger().info("[INFO][PoPr][IDCB----]: Neue Objekte erkannt, Positionen werden aktualisiert.")
            self.bool_no_objects_logged = False

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

    def send_prediction(self, position: tuple[float, float, float, int]) -> None:
        x, y, z, obj_type = position
        msg = NimSortPrediction()
        msg.predicted_position_wcs = Point(x=x, y=y, z=z)
        msg.object_type = obj_type
        self.prediction_pub.publish(msg)

    def publish_predictions(self, positions: list[tuple[float, float, float, int]]) -> None:
        real_objects = [p for p in positions if p[3] != -1]

        if real_objects:
            for position in real_objects:
                self.send_prediction(position)
        elif self.bool_no_objects_logged:
            self.send_prediction(SENTINEL)

    def main_order(self):
        try:
            next_objects = self.logic.calculate_next_object_positions()
        except ValueError as e:
            self.get_logger().warn(str(e))
            return

        self.get_logger().debug(
            f"Objekt {next_objects[0][3]}  | XY: ({next_objects[0][0]:.3f}, {next_objects[0][1]:.3f})\n"
            f"Objekt {next_objects[1][3]} | XY: ({next_objects[1][0]:.3f}, {next_objects[1][1]:.3f})"
        )
        self.publish_predictions(next_objects)


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