"""
axis.py
---
contains the Axis Class for handling one Robotaxis.
"""

from dataclasses import dataclass
from typing import Optional

from nimsort_motion.controller import Controller
from nimsort_motion.trajectroy_planner import TrajectoryPlanner
from nimsort_motion.axis_interface import AxisInterface 

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

class Axis(AxisInterface):
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
    trajectory_planner: TrajectoryPlanner
        Axis-TrajectoryPlanner Class
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
        self._target_position = None
        self._prev_position: float = initial_position

    def set_target(self, target_position: float):
        """
        sets a new target_point and sends the command to the planner.

        Parameters
        ---
        target_position: float [m] position with respect to home
        """
        print(f"[INFO][Axis][setTarg]: Setting new target for Axis {self._name}: {target_position:.4f}m")
        self._target_position = target_position

    def update(self, current_position: float, dt: float) -> float:
        """"
        Zycliclly called function to update the acceleration according to the current_position trough trajectoryPlanner and Controller.
        Input:
        current_position: float [m] position with respect to home
        dt: float [s] time since last update call
        """
        if dt <= 0.0:
            raise ValueError(f"Axis '{self._name}': dt must be positive {dt}.")

        self._velocity = (current_position - self._prev_position) / dt
        self._position = current_position
        self._prev_position = current_position

        target_accel = self._planner.compute(
            target_position = self._target_position,
            current_position = self._position,
            current_velocity = self._velocity
        )

        position_err = self._target_position - self._position
        print(f"[DEBUG][Axis][update--]: pos={self._position:.4f}m, vel={self._velocity:.4f}m/s, tgt={self._target_position:.4f}m, err_p={position_err:.5f}m")

        self._acceleration = self._controller.compute(
            error=position_err,
            dt=dt,
            accel_ff=target_accel
        )
        print(f"[DEBUG][Axis][update--]: acc_out={self._acceleration:.4f}m/s², tgt_acc={target_accel:.4f}m/s², dt={dt:.6f}s")
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
            target_position=self._target_position,
            target_reached=self._planner.reached,
        )
    
    def __repr__(self) -> str:
        return (
            f"Axis('{self._name}' | "
            f"pos={self._position:.4f} m, "
            f"vel={self._velocity:.4f} m/s, "
            f"accel={self._acceleration:.4f} m/s²)"
        )