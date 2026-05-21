from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nimsort_vision.magic_object import MagicObject


class PositionPredictionInterface(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def set_conveyorbelt_speed(self, speed_mps: float) -> None:
        """Setzt die Förderband-Geschwindigkeit in m/s."""
        pass

    @abstractmethod
    def set_object_data(self, object_type: int, position: list[float], ts: int) -> None:
        """Speichert Daten eines erkannten Objekts."""
        pass

    @abstractmethod
    def calculate_next_object_position(self) -> tuple[float, float, float, int, int | None]:
        """Gibt (x, y, z, object_type, obj_id) des führenden Objekts zurück."""
        pass

    @abstractmethod
    def remove_object_by_id(self, obj_id: int) -> None:
        """Entfernt ein Objekt gezielt nach ID."""
        pass

    @property
    @abstractmethod
    def get_stored_objects(self) -> list['MagicObject']:
        """Gibt alle gespeicherten Objekte zurück."""
        pass