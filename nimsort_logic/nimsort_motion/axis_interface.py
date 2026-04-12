from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nimsort_motion.axis import AxisState 

class AxisInterface(ABC):
    @abstractmethod
    def set_target(self, target_position: float) -> None:
        pass

    @abstractmethod
    def update(self, current_position: float, dt: float) -> float:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass

    @property
    @abstractmethod
    def position(self) -> float:
        pass

    @property
    @abstractmethod
    def velocity(self) -> float:
        pass

    @property
    @abstractmethod
    def acceleration(self) -> float:
        pass

    @property
    @abstractmethod
    def target_reached(self) -> bool:
        pass

    @abstractmethod
    def get_state(self) -> "AxisState":
        """Gibt aktuellen Zustand zurück."""
        pass
