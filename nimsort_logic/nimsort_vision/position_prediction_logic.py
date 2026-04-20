from nimsort_vision.magic_object import MagicObject
from nimsort_vision.position_prediction_interface import PositionPredictionInterface
from nimsort_vision.plausibilty_check import PlausibilityCheck


DT = 0.1            # Timer-Intervall in Sekunden
X_THRESHOLD = 40.0   # Schwellwert anpassen #TODO define threshold and document it. According issue: #63


class PositionPrediction(PositionPredictionInterface):

    def __init__(self):
        super().__init__()
        self._conveyor_belt_speed: float = 0.0
        self._objects: dict[int, MagicObject] = {}
        self._object_id_counter: int = 0
        self._plausibility_check = PlausibilityCheck()


    def set_conveyor_belt_speed(self, speed_mps: float) -> None:
        self._conveyor_belt_speed = speed_mps

    def set_object_data(self, object_id: int, object_type: int, position: list[float], ts: int, speed: float = 1.0) -> None:
        self._objects[object_id] = MagicObject(
            object_type=object_type,
            position=position,
            ts=float(ts),
            speed=speed,
        )

    def calculate_next_object_position(self) -> tuple[float, float, float, int]:
        if not self._objects:
            raise ValueError("[WARN]: Keine Objekte gespeichert.")

        if abs(self._conveyor_belt_speed) < 1e-6:
            raise ValueError("[WARN]: Förderband steht still – keine Prädiktion möglich.")

        self._update_positions()

        self._remove_objects_over_threshold()

        if not self._objects:
            raise ValueError("[WARN]: Alle Objekte haben den Schwellwert überschritten.")

        next_obj = self.get_next_object_to_publish()
        return (next_obj.position[0], next_obj.position[1], next_obj.position[2], next_obj.object_type)
    
    @property
    def get_stored_objects(self) -> list[MagicObject]:
        return list(self._objects.values())

    @property
    def get_conveyor_belt_speed(self) -> float:
        return self._conveyor_belt_speed

    def get_next_object_to_publish(self) -> MagicObject:
        """Gibt das Objekt mit der größten X-Position zurück."""
        if not self._objects:
            raise ValueError("[WARN]: Keine Objekte verfügbar zum Publizieren.")
        
        next_obj = max(self._objects.values(), key=lambda obj: obj.position[0])
        
        if not self._plausibility_check.check_position(next_obj.position):
            raise ValueError("[WARN]: Ausgabe-Position hat Plausibilitätsprüfung nicht bestanden.")
        
        return next_obj

    def _update_positions(self) -> None: 
        """X-Position aller Objekte um speed * dt erhöhen."""
        updated_objects = {}
        for obj in self._objects.values():
            x_new = obj.position[0] + self._conveyor_belt_speed * DT
            updated_obj = MagicObject(
                object_type=obj.object_type,
                position=[x_new, obj.position[1], obj.position[2]],
                ts=obj.ts,
                speed=obj.speed,
            )
            object_id = self._object_id_counter
            self._object_id_counter += 1
            updated_objects[object_id] = updated_obj
        self._objects = updated_objects

    def _remove_objects_over_threshold(self) -> None:
        """Objekte deren X-Position den Schwellwert überschreitet entfernen."""
        to_remove = [
            object_type
            for object_type, obj in self._objects.items()
            if obj.position[0] >= X_THRESHOLD
        ]
        for object_type in to_remove:
            print(f"[PoPr][ROOT----][INFO]: Objekt {object_type} hat Schwellwert erreicht – wird entfernt.") 
            del self._objects[object_type]