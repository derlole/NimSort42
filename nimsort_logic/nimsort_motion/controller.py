from nimsort_motion.controller_interface import ControllerInterface
from nimsort_motion.kalman_filter import KalmanFilterPosVel

"""
controller.py
---
PDF-Controller Class for handling the control of one Robotaxis.
---
"""

class Controller(ControllerInterface):
    """
    PDF-Regler (Proportional + filtered Derivative + filtered Feedforward)

    Parameters
    ---
    kp : float
    kd : float

    use_derivative_filter : bool
    d_filter_alpha : float  (0 < alpha < 1)
        Smoothing coefficient for d-component

    use_feedforward : bool
    tf : float  [s]    
        Time constant for FF low-pass filter.
        tf = 0.0 → no FF-filter
    """
    def __init__(
        self,
        kp: float,
        kd: float,
        output_limit: float,
        kff: float = 0.0,
        q_pos=1e-4,
        q_vel=1e-2,
        r=1e-1
    ):
        self.kp = kp
        self.kd = kd
        self.kff = kff

        self._min, self._max = -output_limit, output_limit
        self._last_error = 0.0
        self._first = True

        self.kalman = KalmanFilterPosVel(q_pos, q_vel, r)
        
    def reset(self):
        self._last_error = 0.0
        self._first = True

    def compute(self, error: float, dt: float, accel_ff: float = 0.0):
        if dt <= 0.0:
            raise ValueError("dt must be positive")

        p = self.kp * error

        if self._first:
            d = 0.0
            self._first = False
        else:
            d = self.kd * (error - self._last_error) / dt

        self._last_error = error

        output = p + d + self.kff * accel_ff

        return self._clamp(output)
    def _clamp(self, value):
        if self._min is not None:
            value = max(self._min, value)
        if self._max is not None:
            value = min(self._max, value)
        return value       
