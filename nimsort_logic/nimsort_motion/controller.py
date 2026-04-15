from nimsort_motion.controller_interface import ControllerInterface

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
        d_filter_alpha: float,
        tf: float,
        max_acceleration: float,
        min_acceleration: float,

        use_derivative_filter: bool = False,
        use_feedforward: bool = False,
    ):
        if kp < 0 or kd < 0:
            raise ValueError("kp and kd must be non negative")
        if not (0.0 < d_filter_alpha < 1.0):
            raise ValueError("d_filter_alpha must be within (0, 1)")
        if tf < 0.0:
            raise ValueError("tf must be non negative")

        self.kp = kp
        self.kd = kd

        self.use_derivative_filter = use_derivative_filter
        self.d_filter_alpha = d_filter_alpha

        self.use_feedforward = use_feedforward
        self.tf = tf

        self.max_acceleration = max_acceleration
        self.min_acceleration = (
            -max_acceleration
            if (min_acceleration is None and max_acceleration is not None)
            else min_acceleration
        )

        self._d_filtered: float = 0.0    # gefilterter Geschwindigkeitsfehler
        self._ff_filtered: float = 0.0   # gefilterter Feedforward-Wert

    def reset(self):
        """resets filters after unexpected Stop or restart"""
        self._d_filtered = 0.0
        self._ff_filtered = 0.0

    def compute(self, position_error: float, velocity_error: float, target_acceleration: float,  dt: float):
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
        if dt <= 0.0:
            raise ValueError(f"dt must be positiv, current value is {dt}.")
        
        p_term = self.kp * position_error

        if self.use_derivative_filter:
            self._d_filtered = ((1.0 - self.d_filter_alpha) * self._d_filtered + self.d_filter_alpha * velocity_error)
            d_term = self.kd * self._d_filtered
        else:
            d_term = self.kd * velocity_error

        if self.use_feedforward:
            if self.tf > 0.0:
                beta = dt / (self.tf + dt)
                self._ff_filtered = ((1.0 - beta) * self._ff_filtered + beta * target_acceleration)
                ff_term = self._ff_filtered
            else:
                ff_term = target_acceleration
        else:
            ff_term = 0.0

        acceleration = p_term + d_term + ff_term

        if self.max_acceleration is not None:
            acceleration = min(acceleration, self.max_acceleration)
        if self.min_acceleration is not None:
            acceleration = max(acceleration, self.min_acceleration)

        return acceleration