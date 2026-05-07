from nimsort_vision.magic_object import MagicObject
from nimsort_vision.position_prediction_interface import PositionPredictionInterface
from nimsort_vision.plausibility_check import PlausibilityCheck
 
DT = 0.1
X_THRESHOLD = 0.55
DUPLICATE_THRESHOLD = 0.06  # Maximaler Abstand in X, um Objekte als Duplikate zu betrachten
SENTINEL_POSITION = [-1.0, -1.0, -1.0]
SENTINEL_TYPE = -1
 
class PositionPrediction(PositionPredictionInterface):
 
    def __init__(self):
        super().__init__()
        self._conveyor_belt_speed = None
        self._objects: dict[int, MagicObject] = {}
        self._over_threshold_objects: list[MagicObject] = []
        self._object_id_counter: int = 0
        self._plausibility_check = PlausibilityCheck()
 
    def set_conveyor_belt_speed(self, conveyor_belt_speed: float) -> None:
        self._conveyor_belt_speed = conveyor_belt_speed
 
    def set_object_data(self, object_type: int, position: list[float], ts: int) -> None:
        """
        Speichert ein Objekt mit eindeutiger ID.
 
        Falls ein ähnliches Objekt (anhand X-Position) bereits existiert,
        wird der Mittelwert von X und Y gebildet statt ein neues Objekt anzulegen.
        """
        existing = self._find_similar_object(position[0])
 
        if existing is not None:
            old_x, old_y = existing.position[0], existing.position[1]
            existing.position[0] = (old_x + position[0]) / 2.0
            existing.position[1] = (old_y + position[1]) / 2.0
            print(
                f"[INFO][PoPr][SOD-----]: Objekt aktualisiert – "
                f"X: {old_x:.3f} → {existing.position[0]:.3f}, "
                f"Y: {old_y:.3f} → {existing.position[1]:.3f}"
            )
            return
        if position[0] >= DUPLICATE_THRESHOLD:
            new_id = self._object_id_counter
            self._object_id_counter += 1
            self._objects[new_id] = MagicObject(
                object_type=object_type,
                position=position,
                ts=float(ts),
            )
 
        print(f"[INFO][PoPr][SOD-----]: Objekt mit ID {new_id} bei X={position[0]:.2f} gespeichert.")
 
    def get_next_objects_to_publish(self, n: int = 2) -> list[MagicObject]:
        """Gibt die n Objekte mit der größten X-Position zurück."""
        if not self._objects:
            raise ValueError("[WARN][PoPr][GNOTP---]: Keine Objekte verfügbar.")
 
        sorted_objs = sorted(
            self._objects.values(),
            key=lambda obj: obj.position[0],
            reverse=True
        )[:n]
 
        for obj in sorted_objs:
            if obj.object_type == SENTINEL_TYPE and obj.position[:3] == SENTINEL_POSITION:
                continue
            if not self._plausibility_check.check_position(obj.position):
                raise ValueError("[WARN][PoPr][GNOTP---]: Ausgabe-Position hat Plausibilitätsprüfung nicht bestanden.")
 
        return sorted_objs
 
    def calculate_next_object_positions(self) -> list[tuple[float, float, float, int]]:
        """
        Berechnet die nächsten Positionen der führenden Objekte.
        Update und Threshold-Entfernung passiert genau einmal hier.
        """
        if self._conveyor_belt_speed is None or self._conveyor_belt_speed < 0:
            raise ValueError("[WARN][PoPr][CNOP----]: Förderband-Geschwindigkeit ungültig.")
 
        self._update_positions()
        self._remove_objects_over_threshold()
 
        if not self._objects:
            return [-1.0, -1.0, -1.0, -1], [-1.0, -1.0, -1.0, -1]  
 
        candidates = self.get_next_objects_to_publish(n=2)
 
        return [
            (obj.position[0], obj.position[1], obj.position[2], obj.object_type)
            for obj in candidates
        ]
 
    @property
    def get_stored_objects(self) -> list[MagicObject]:
        return list(self._objects.values())
 
    @property
    def get_over_threshold_objects(self) -> list[MagicObject]:
        """Objekte die den X_THRESHOLD überschritten haben und entfernt wurden."""
        return list(self._over_threshold_objects)
 
    @property
    def get_conveyor_belt_speed(self) -> float:
        return self._conveyor_belt_speed
 
    def get_next_object_to_publish(self) -> MagicObject:
        """Gibt das Objekt mit der größten X-Position zurück."""
        if not self._objects:
            return [-1.0, -1.0, -1.0, -1]  
        next_obj = max(self._objects.values(), key=lambda obj: obj.position[0])
        if next_obj.object_type == SENTINEL_TYPE and next_obj.position[:3] == SENTINEL_POSITION:
            return next_obj
        if not self._plausibility_check.check_position(next_obj.position):
            raise ValueError("[WARN][PoPr][GNOTP---]: Ausgabe-Position hat Plausibilitätsprüfung nicht bestanden.")
        return next_obj
 
    def _update_positions(self) -> None:
        """X-Position aller Objekte um speed * dt erhöhen."""
        for obj in self._objects.values():
            obj.position[0] += self._conveyor_belt_speed * DT
 
    def _remove_objects_over_threshold(self) -> None:
        """
        Objekte deren X-Position den Schwellwert überschreitet entfernen.
 
        Entfernte Objekte werden in _over_threshold_objects gespeichert.
        """
        for obj_id, obj in list(self._objects.items()):
            if obj.position[0] >= X_THRESHOLD:
                self._over_threshold_objects.append(obj)
                del self._objects[obj_id]
                print(
                    f"[INFO][PoPr][ROOT----]: Objekt ID {obj_id} bei X={obj.position[0]:.2f} "
                    f"über Threshold – in over_threshold_objects verschoben."
                )
 
    def _find_similar_object(self, x_position: float) -> MagicObject | None:
        """
        Sucht ein bestehendes Objekt dessen X-Position innerhalb DUPLICATE_THRESHOLD liegt.
 
        Gibt das erste Treffer-Objekt zurück, oder None falls keines gefunden wurde.
        """
        for obj in self._objects.values():
            if abs(obj.position[0] - x_position) < DUPLICATE_THRESHOLD:
                return obj
        return None
 
