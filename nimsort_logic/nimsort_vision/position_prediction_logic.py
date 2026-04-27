from nimsort_vision.magic_object import MagicObject
from nimsort_vision.position_prediction_interface import PositionPredictionInterface
from nimsort_vision.plausibility_check import PlausibilityCheck


DT = 0.1            # Timer-Intervall in Sekunden
X_THRESHOLD = 0.4   # Schwellwert anpassen #TODO define threshold and document it. According issue: #63
DUPLICATE_THRESHOLD = 0.03  # X-Position Differenz um Duplikate zu erkennen

class PositionPrediction(PositionPredictionInterface):

    def __init__(self):
        super().__init__()
        self._conveyor_belt_speed = None
        self._objects: dict[int, MagicObject] = {}
        self._object_id_counter: int = 0
        self._plausibility_check = PlausibilityCheck()


    def set_conveyor_belt_speed(self, conveyor_belt_speed: float) -> None:
        self._conveyor_belt_speed = conveyor_belt_speed

    def set_object_data(self, object_type: int, position: list[float], ts: int) -> None:
        """
        Speichert ein Objekt mit eindeutiger ID.
        Duplikate werden anhand der X-Position erkannt und ignoriert.
        """
       
        if self._is_duplicate(position[0]):
            print(f"[WARN][PoPr][ROOT----]: Duplikat erkannt bei X={position[0]:.2f} – wird ignoriert.")
            return
        new_id = self._object_id_counter
        self._object_id_counter += 1
        
        self._objects[new_id] = MagicObject(
            object_type=object_type,
            position=position,
            ts=float(ts),
        )
        print(f"[INFO][PoPr][ROOT----]: Objekt mit ID {new_id} bei X={position[0]:.2f} gespeichert.")

    def calculate_next_object_position(self) -> tuple[float, float, float, int]:
        if (self._conveyor_belt_speed < 1e-6) or self._conveyor_belt_speed is None:
            raise ValueError("[WARN]: Förderband steht still – keine Prädiktion möglich.")

        self._update_positions()
        self._remove_objects_over_threshold()

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
            raise ValueError("[WARN]: Keine Objekte verfügbar.")
        
        next_obj = max(self._objects.values(), key=lambda obj: obj.position[0])
        
        if not self._plausibility_check.check_position(next_obj.position):
            raise ValueError("[WARN]: Ausgabe-Position hat Plausibilitätsprüfung nicht bestanden.")
        
        return next_obj

    def _update_positions(self) -> None:
        """X-Position aller Objekte um speed * dt erhöhen."""
        for obj in self._objects.values():
            obj.position[0] += self._conveyor_belt_speed * DT

    def _remove_objects_over_threshold(self) -> None:
        """Objekte deren X-Position den Schwellwert überschreitet entfernen."""
        for obj_id, obj in list(self._objects.items()):
            if obj.position[0] >= X_THRESHOLD:
                del self._objects[obj_id]

    def _is_duplicate(self, x_position: float) -> bool:
        """
        Prüft ob bereits ein Objekt unter der Schwelle liegt um bereits abgespeichert zu sein.
        """
        for obj in self._objects.values():
            if abs(obj.position[0] - x_position) < DUPLICATE_THRESHOLD:
                return True
                
        return False