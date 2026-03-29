"""
axis.py
---
contains the Axis Class for handling one Robotaxis.
"""

from dataclasses import dataclass
from typing import Optional

from nimsort_motion.controller import Controller

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
    def __init__(self, name: str, controller:  Controller, initial_position: float = 0.0):
        self._name = name
        self._controller = controller

        self._position = initial_position
        self._velocity = 0.0
        self._acceleration = 0.0

        self._prev_position: float = initial_position
