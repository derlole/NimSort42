from nimsort_vision.magic_object import MagicObject
from .position_prediction_interface import PositionPredictionInterface


DT = 0.1            # Timer-Intervall in Sekunden
X_THRESHOLD = 40.0   # Schwellwert anpassen


class PositionPrediction(PositionPredictionInterface):

    def __init__(self):
        super().__init__()
        self._conveyor_belt_speed: float = 0.0
        self._objects: dict[int, MagicObject] = {}


    def set_conveyor_belt_speed(self, speed_mps: float) -> None:
        self._conveyor_belt_speed = speed_mps

    def set_object_data(self, object_type: int, position: tuple[float, float, float], ts: int) -> None:
        self._objects[object_type] = MagicObject(
            object_type=object_type,
            position=position,
            ts=float(ts),
        )

    def calculate_next_object_position(self) -> tuple[float, float, float, int]:
        if not self._objects:
            raise ValueError("Keine Objekte gespeichert.")

        if abs(self._conveyor_belt_speed) < 1e-6:
            raise ValueError("Förderband steht still – keine Prädiktion möglich.")

        # X für alle Objekte aufaddieren
        self._update_positions()

        # Objekte über Schwellwert entfernen
        self._remove_objects_over_threshold()

        if not self._objects:
            raise ValueError("Alle Objekte haben den Schwellwert überschritten.")

        # Objekt mit größter X-Position publizieren
        next_obj = max(self._objects.values(), key=lambda obj: obj.position[0])
        return (next_obj.position[0], next_obj.position[1], next_obj.position[2], next_obj.object_type)

    @property
    def get_stored_objects(self) -> list[MagicObject]:
        return list(self._objects.values())

    @property
    def get_conveyor_belt_speed(self) -> float:
        return self._conveyor_belt_speed

   

    def _update_positions(self) -> None:
        """X-Position aller Objekte um speed * dt erhöhen."""
        for object_type, obj in self._objects.items():
            x_new = obj.position[0] + self._conveyor_belt_speed * DT
            self._objects[object_type] = MagicObject(
                object_type=obj.object_type,
                position=(x_new, obj.position[1], obj.position[2]),
                ts=obj.ts,
            )

    def _remove_objects_over_threshold(self) -> None:
        """Objekte deren X-Position den Schwellwert überschreitet entfernen."""
        to_remove = [
            object_type
            for object_type, obj in self._objects.items()
            if obj.position[0] >= X_THRESHOLD
        ]
        for object_type in to_remove:
            print(f"[PositionPrediction] Objekt {object_type} hat Schwellwert erreicht – wird entfernt.")
            del self._objects[object_type]