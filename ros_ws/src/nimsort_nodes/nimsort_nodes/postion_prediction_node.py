import time
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from std_msgs.msg import Bool
from nimsort_msgs.msg import NimSortPrediction, NimSortImageData, NimSortConveyorbeltSpeed
from geometry_msgs.msg import Point
from nimsort_vision.position_prediction_logic import PositionPrediction as PositionPredictionLogic

DEFAULT_CONVEYOR_BELT_SPEED = 0.01



class PositionPredictionNode(Node):

    def __init__(self):
        super().__init__('position_prediction_node')
        self.logic = PositionPredictionLogic()
        self.logic.set_conveyorbelt_speed(DEFAULT_CONVEYOR_BELT_SPEED)

       
        self._waiting_for_feedback: bool = False
        self._published_object_id: int | None = None   
        
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
        self.feedback_sub = self.create_subscription(
            Bool,
            '/NimSortPredictionFeedback',
            self.feedback_callback,
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

    def feedback_callback(self, msg: Bool):
        """
        True  = Objekt verbraucht → gezielt nach ID löschen, nächstes publishen (#2)
        False = Objekt akzeptiert → weiter warten
        Feedback auf Sentinel (published_object_id is None) wird ignoriert (#4)
        """
        if self._published_object_id is None:
            
            self.get_logger().debug('[PoPr][feedback]: Feedback auf Sentinel ignoriert.')
            return

        if msg.data:  # True = verbraucht / abgelehnt
            self.logic.remove_object_by_id(self._published_object_id)
            self._release_feedback_state()
            self.get_logger().debug(
                f'[PoPr][feedback]: Objekt ID {self._published_object_id} entfernt, bereit für nächstes.'
            )
        else:  # False = akzeptiert, MainNode greift es
            self.get_logger().debug('[PoPr][feedback]: Objekt akzeptiert, warte auf Verbrauch.')

    def _release_feedback_state(self) -> None:
        """Setzt Feedback-State zurück."""
        self._waiting_for_feedback = False
        self._published_object_id = None
        

    def _publish_prediction(self, x: float, y: float, z: float, obj_type: int) -> None:
        msg = NimSortPrediction()
        msg.predicted_position_wcs = Point(x=x, y=y, z=z)
        msg.object_type = obj_type
        self.prediction_pub.publish(msg)

    def main_order(self):
        if time.time() - self.last_image_data_time > 1.0:
            self.get_logger().warning('[PoPr][main_ord]: Keine aktuellen ImageData, Killing myself.')
            raise RuntimeError('Keine aktuellen ImageData, Killing myself.')

     
        if self._waiting_for_feedback:
            if self._published_object_id is not None:
                self.logic.remove_object_by_id(self._published_object_id)
                self._release_feedback_state()
            else:
                return  

        try:
            x, y, z, obj_type, obj_id = self.logic.calculate_next_object_position()
        except ValueError as e:
            self.get_logger().warn(str(e))
            return

        self._publish_prediction(x, y, z, obj_type)

        if obj_id is None:
            
            self.get_logger().debug('[PoPr][main_ord]: Sentinel published, kein Feedback erwartet.')
            self._waiting_for_feedback = False
            self._published_object_id = None
        else:
           
            self._waiting_for_feedback = True
            self._published_object_id = obj_id
            self.get_logger().debug(
                f'[PoPr][main_ord]: Objekt ID {obj_id} published, warte auf Feedback.'
            )


def main(args=None):
    rclpy.init(args=args)
    node = PositionPredictionNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except (ExternalShutdownException, KeyboardInterrupt):
        node.get_logger().error('[PoPr][main----]: Shutdown Node')
    except RuntimeError as e:
        node.get_logger().error(f'[PoPr][main----]: {str(e)}')
    finally:
        executor.shutdown()
        rclpy.shutdown()


if __name__ == '__main__':
    main()