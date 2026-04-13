from abc import ABC, abstractmethod

class InitProcessInterface(ABC):
    
    @abstractmethod
    def start(self) -> None:
        """Start the initialization process."""
        pass

    def robot_values(self, position: tuple[float, float, float]) -> tuple[float, float, float]:
        """Set the initial values for the process. and return the corresponding acceleration commands."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the initialization process."""
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if the initialization process is complete."""
        pass