from abc import ABC, abstractmethod

class TrajectoryPlannerInterface(ABC):

    @abstractmethod
    def compute(self, current_position: float, current_velocity: float, dt: float) -> tuple[float, float, float]:
        """
        calculates values for current cycle
        Parameters
        ---
        current_position: flaot [m]
        current_velocity [m/s]
        dt [s]

        Returns
        ---
        tuple[float, float, float]
            (target_position, target_velocity, target_acceleration)
        """
        pass

    @property
    @abstractmethod
    def reached(self) -> bool:
        pass