"""
axis.py
---
contains the Axis Class for handling one Robotaxis.
"""

from dataclasses import dataclass
from typing import Optional

from nimsort_motion.controller import Controller
from nimsort_motion.trajectroy_planner import TrajectoryPlanner

@dataclass
class AxisState:
    """
    Spnapshot of the axisstate for logging and debugging
    ---
    returns:
    position: float (Axis position relative to home [m])
    velocity: float (Velocity of the robotaxis in [m/s])
    acceleration: float (last calculated target acceleration [m/s^2])
    target_position:  float = 0.0 (current target position)
    """
    position: float = 0.0
    velocity: float = 0.0
    acceleration: float = 0.0
    target_position: float = 0.0
    target_reached: bool = True

class Axis:
    """
    Class for handling one Robotaxis.
    contains and handles the state of one axis
    ---
    Parameters
    ---
    name: str
        axis-name e.g. "X"
    controller: Controller
        Axis-Controller Class
    initial_position: float
        Initial Axis Position [m] (should be 0.0)

    """
    def __init__(self, name: str, controller:  Controller, trajectory_planner: TrajectoryPlanner, initial_position: float = 0.0):
        self._name = name
        self._controller = controller
        self._planner = trajectory_planner

        self._position = initial_position
        self._velocity = 0.0
        self._acceleration = 0.0

        self._prev_position: float = initial_position

    def set_target(self, target_position: float):
        """
        sets a new target_point and sends the command to the planner.

        Parameters
        ---
        target_position: float [m]
        """
        self._planner.set_target(target_position)

    def update(self, current_position: float, dt: float) -> float:
        """"
        Zycliclly called function to update the acceleration accourding to the current_position trough trajectoryPlanner and Controller.
        """
        if dt <= 0.0:
            raise ValueError(f"Axis '{self.name}': dt muss positiv sein, ist {dt}.")

        self._velocity = (current_position - self._prev_position) / dt
        self._position = current_position
        self._prev_position = current_position

        target_pos, target_vel, target_accel = self._planner.step(
            current_position = self._position,
            current_velocity = self._velocity,
            dt = dt
        )

        position_err = target_pos - self._position
        velocity_err = target_vel - self._velocity

        self._acceleration = self._controller.compute(
            position_error=position_err,
            velocity_error=velocity_err,
            dt=dt,
            target_acceleration=target_accel
        )

        return self._acceleration
    
    def reset(self) -> None:
        """
        resets axisstate and controller to initial state
        """
        self._position = 0.0
        self._velocity = 0.0
        self._acceleration = 0.0
        self._prev_position = 0.0
        self._controller.reset()

    @property
    def position(self) -> float:
        """current position [m]."""
        return self._position

    @property
    def velocity(self) -> float:
        """current velocity [m/s]."""
        return self._velocity

    @property
    def acceleration(self) -> float:
        """current acceleration [m/s²]."""
        return self._acceleration

    @property
    def target_reached(self) -> bool:
        """True wenn die Achse den Zielpunkt erreicht hat und steht."""
        return self._planner.reached
    
    def get_state(self) -> AxisState:
        """Gibt einen Schnappschuss des aktuellen Zustands zurück."""
        return AxisState(
            position=self._position,
            velocity=self._velocity,
            acceleration=self._acceleration,
            target_position=self._planner.target_position,
            target_reached=self._planner.reached,
        )
    
    def __repr__(self) -> str:
        return (
            f"Axis('{self.name}' | "
            f"pos={self._position:.4f} m, "
            f"vel={self._velocity:.4f} m/s, "
            f"accel={self._acceleration:.4f} m/s²)"
        )