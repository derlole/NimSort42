from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
 
if TYPE_CHECKING:
    from nimsort_vision.magic_object import MagicObject
 
 
class PositionPredictionInterface(ABC):
 
    def __init__(self):
        """Initialize the Position Prediction."""
        pass
 
    @abstractmethod
    def set_conveyor_belt_speed(self, speed_mps: float) -> None:
        """Set the conveyor belt speed in meters per second."""
        pass
 
    @abstractmethod
    def set_object_data(self, object_id: int, object_type: int, position: list[float], ts: int, speed: float = 1.0) -> None:
        """Set the data for a detected object."""
        pass
 
    @abstractmethod
    def calculate_next_object_position(self) -> tuple[float, float, float, int]:
        """Returns (x, y, z, object_type) of the next arriving object."""
        pass
 
    @abstractmethod
    def get_next_object_to_publish(self) -> 'MagicObject':
        """Returns the MagicObject with the highest X-Position."""
        pass
 
    @property
    @abstractmethod
    def get_stored_objects(self) -> list['MagicObject']:
        """Get the stored objects."""
        pass
 
    @property
    @abstractmethod
    def get_conveyor_belt_speed(self) -> float:
        """Get the current conveyor belt speed."""
        pass
 