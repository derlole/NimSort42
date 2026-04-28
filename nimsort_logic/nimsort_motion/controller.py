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

        self.kalman = KalmanFilterPosVel(q_pos, q_vel, r)
        
    def reset(self):
        self.kalman.reset()

    def compute(self, error:float, dt: float, accel_ff: float = 0.0):
        if dt <= 0.0:
           raise ValueError("dt must be positive")
       
        pos, vel = self.kalman.update(error, dt)

        p = self.kp * pos
        d = self.kd * vel
        output = p + d + self.kff * accel_ff

        return self._clamp(output)

    def _clamp(self, value):
        if self._min is not None:
            value = max(self._min, value)
        if self._max is not None:
            value = min(self._max, value)
        return value       
