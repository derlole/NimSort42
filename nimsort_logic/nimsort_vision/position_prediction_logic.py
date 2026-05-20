from nimsort_vision.magic_object import MagicObject
from nimsort_vision.position_prediction_interface import PositionPredictionInterface
from nimsort_vision.plausibility_check import PlausibilityCheck

DT = 0.1
X_THRESHOLD = 0.55
DUPLICATE_THRESHOLD = 0.06
SENTINEL_POSITION = [-1.0, -1.0, -1.0]
SENTINEL_TYPE = -1


class PositionPrediction(PositionPredictionInterface):

    def __init__(self):
        super().__init__()
        self._conveyor_belt_speed: float | None = None
        self._objects: dict[int, MagicObject] = {}
        self._over_threshold_objects: list[MagicObject] = []
        self._object_id_counter: int = 0
        self._plausibility_check = PlausibilityCheck()

    def set_conveyorbelt_speed(self, conveyor_belt_speed: float) -> None:
        self._conveyor_belt_speed = conveyor_belt_speed

    def set_object_data(self, object_type: int, position: list[float], ts: int) -> None:
        existing = self._find_similar_object(position[0])

        if existing is not None:
            old_x, old_y = existing.position[0], existing.position[1]
            existing.position[0] = (old_x + position[0]) / 2.0
            existing.position[1] = (old_y + position[1]) / 2.0
            print(
                f'[INFO][PoPr][SOD-----]: Objekt aktualisiert – '
                f'X: {old_x:.3f} → {existing.position[0]:.3f}, '
                f'Y: {old_y:.3f} → {existing.position[1]:.3f}'
            )
            return

        if position[0] < DUPLICATE_THRESHOLD:
            return

        new_id = self._object_id_counter
        self._object_id_counter += 1
        self._objects[new_id] = MagicObject(
            object_type=object_type,
            position=position,
            ts=float(ts),
        )
        print(f'[INFO][PoPr][SOD-----]: Objekt ID {new_id} bei X={position[0]:.3f} gespeichert.')

    def remove_object_by_id(self, obj_id: int) -> None:
        """Entfernt gezielt das Objekt mit der gegebenen ID (Fix #2)."""
        if obj_id in self._objects:
            removed = self._objects.pop(obj_id)
            print(f'[INFO][PoPr][ROBI----]: Objekt ID {obj_id} bei X={removed.position[0]:.3f} entfernt.')
        else:
            print(f'[WARN][PoPr][ROBI----]: Objekt ID {obj_id} nicht gefunden, bereits entfernt?')

    def calculate_next_object_position(self) -> tuple[float, float, float, int, int | None]:
        """
        Updatet alle Positionen, entfernt Threshold-Überschreiter,
        gibt (x, y, z, object_type, obj_id) zurück.
        obj_id ist None wenn kein Objekt vorhanden (Sentinel).
        """
        if self._conveyor_belt_speed is None or self._conveyor_belt_speed < 0:
            raise ValueError('[WARN][PoPr][CNOP----]: Förderband-Geschwindigkeit ungültig.')

        self._update_positions()
        self._remove_objects_over_threshold()

        if not self._objects:
            return (-1.0, -1.0, -1.0, -1, -1) 
         
        leading_id = max(self._objects, key=lambda k: self._objects[k].position[0])
        leading = self._objects[leading_id]

        if not self._plausibility_check.check_position(leading.position):
            raise ValueError('[WARN][PoPr][CNOP----]: Plausibilitätsprüfung fehlgeschlagen.')

        return (
            leading.position[0],
            leading.position[1],
            leading.position[2],
            leading.object_type,
            leading_id,          #
        )


    @property
    def get_stored_objects(self) -> list[MagicObject]:
        return list(self._objects.values())

    @property
    def get_over_threshold_objects(self) -> list[MagicObject]:
        return list(self._over_threshold_objects)

    @property
    def get_conveyor_belt_speed(self) -> float | None:
        return self._conveyor_belt_speed

    # ── Private ───────────────────────────────────────────────────────────────

    def _update_positions(self) -> None:
        for obj in self._objects.values():
            obj.position[0] += self._conveyor_belt_speed * DT

    def _remove_objects_over_threshold(self) -> None:
        for obj_id, obj in list(self._objects.items()):
            if obj.position[0] >= X_THRESHOLD:
                self._over_threshold_objects.append(obj)
                del self._objects[obj_id]
                print(
                    f'[INFO][PoPr][ROOT----]: Objekt ID {obj_id} bei X={obj.position[0]:.3f} '
                    f'über {X_THRESHOLD:.3f} entfernt.'
                )

    def _find_similar_object(self, x_position: float) -> MagicObject | None:
        for obj in self._objects.values():
            if abs(obj.position[0] - x_position) < DUPLICATE_THRESHOLD:
                return obj
        return None