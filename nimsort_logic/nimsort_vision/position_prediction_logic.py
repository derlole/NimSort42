from nimsort_vision.magic_object import MagicObject
from nimsort_vision.position_prediction_interface import PositionPredictionInterface
from nimsort_vision.plausibility_check import PlausibilityCheck


DT = 0.1            # Timer-Intervall in Sekunden
X_THRESHOLD = 40.0   # Schwellwert anpassen #TODO define threshold and document it. According issue: #63
DUPLICATE_THRESHOLD = 0.03  # X-Position Differenz um Duplikate zu erkennen
DEFAULT_CONVEYOR_BELT_SPEED = 0.01 # Standard, delet when measurement is done 

class PositionPrediction(PositionPredictionInterface):

    def __init__(self):
        super().__init__()
        self._conveyor_belt_speed: float = DEFAULT_CONVEYOR_BELT_SPEED
        self._objects: dict[int, MagicObject] = {}
        self._object_id_counter: int = 0
        self._plausibility_check = PlausibilityCheck()


    def set_conveyor_belt_speed(self, speed_mps: float) -> None:
        self._conveyor_belt_speed = speed_mps

    def set_object_data(self, object_type: int, position: list[float], ts: int, speed: float = 1.0) -> None:
        """
        Speichert ein Objekt mit eindeutiger ID.
        Duplikate werden anhand der X-Position erkannt und ignoriert.
        """
       
        if self._is_duplicate(position[0]):
            print(f"[PoPr][ROOT----][WARN]: Duplikat erkannt bei X={position[0]:.2f} – wird ignoriert.")
            return
        
  
        new_id = self._object_id_counter
        self._object_id_counter += 1
        
        self._objects[new_id] = MagicObject(
            object_type=object_type,
            position=position,
            ts=float(ts),
            speed=speed,
        )
        print(f"[PoPr][ROOT----][INFO]: Objekt mit ID {new_id} bei X={position[0]:.2f} gespeichert.")

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
        for obj_id, obj in self._objects.items():  # ← ID beibehalten
            x_new = obj.position[0] + self._conveyor_belt_speed * DT
            self._objects[obj_id] = MagicObject(
                object_type=obj.object_type,
                position=[x_new, obj.position[1], obj.position[2]],
                ts=obj.ts,
                speed=obj.speed,
        )
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

    def _is_duplicate(self, x_position: float) -> bool:
        """
        Prüft ob bereits ein Objekt mit ähnlicher X-Position existiert.
        """
        for obj in self._objects.values():
            if abs(obj.position[0] - x_position) < DUPLICATE_THRESHOLD:
                return True
        return False