from abc import ABC, abstractmethod

class ControllerInterface(ABC):
    @abstractmethod
    def reset(self) -> None:
        pass

    @abstractmethod
    def compute(self, position_error: float, velocity_error: float, target_acceleration: float, dt: float) -> float:
        """
        compute the control output for a single time step

        Parameters
        ---
        position_error : float [m]
        velocity_error : float [m/s]
        dt : float [s]
        target_acceleration : float [m/s²].

        Returns
        ---
        float
            target_acceleration [m/s²]
        """
        pass