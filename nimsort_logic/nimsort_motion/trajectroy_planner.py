class TrajectoryPlanner:
    """
    Feedforward-Trajectory Planner (nur Beschleunigung)

    Parameters
    ---
    max_velocity : float [m/s]
    max_acceleration : float [m/s²]
    """

    def __init__(self, max_velocity: float, max_acceleration: float):
        if max_velocity <= 0:
            raise ValueError("max_velocity has to be positive")
        if max_acceleration <= 0:
            raise ValueError("max_acceleration has to be positive")

        self.max_velocity = max_velocity
        self.max_acceleration = max_acceleration
        self._reached = False

    # ─────────────────────────────────────────────

    def compute(
        self,
        target_position: float,
        current_position: float,
        current_velocity: float,
    ) -> float:
        """
        Berechnet Feedforward-Beschleunigung

        Parameters
        ---
        target_position : float [m]
        current_position : float [m]
        current_velocity : float [m/s]

        Returns
        ---
        float : target_acceleration [m/s²]
        """

        distance = target_position - current_position
        direction = 1.0 if distance >= 0.0 else -1.0

        brake_distance = (current_velocity ** 2) / (2.0 * self.max_acceleration)
        wrong_direction = (current_velocity * direction) < 0.0
        braking_needed = abs(distance) <= brake_distance

        if braking_needed or wrong_direction:
            velocity_sign = 1.0 if current_velocity >= 0.0 else -1.0
            acc = -velocity_sign * self.max_acceleration

        elif abs(current_velocity) < self.max_velocity:
            acc = direction * self.max_acceleration
        else:
            acc = 0.0

        if abs(distance) < 0.0001 and abs(current_velocity) < 0.001:
            self._reached = True
        else:
            self._reached = False
            
        return acc


    @property
    def reached(self) -> bool:
        return self._reached