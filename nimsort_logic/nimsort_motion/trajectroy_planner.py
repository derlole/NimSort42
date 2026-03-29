"""
trajectory_planner.py
---
contains class for incremental trajectory planner for one axis
"""

class TrajectoryPlanner:
    """
    incremental trajectory planner for one axis
    Parameters
    ---
    max_velocity : float [m/s].
    max_acceleration : float [m/s²].
    position_tolerance : float [m].
    velocity_tolerance : float [m/s].
    """
    def __init__(self, max_velocity: float, max_acceleration: float, position_tolerance: float, velocity_tolerance: float):
        if max_velocity <= 0:
            raise ValueError("max_velocity has to be positive")
        if max_acceleration <= 0:
            raise ValueError("max_acceleration has to be positive")
        
        self.max_veloity = max_velocity
        self.max_acceleration = max_acceleration
        self.position_tolerance = position_tolerance
        self.velocity_tolerance = velocity_tolerance

        self._target_position: float = 0.0
        self._reached: bool = True
    
    def set_target(self, target_position: float):
        """
        sets a new target point even if another movement is already executed
        Parameters
        ---
        target_position: float [m]
        """
        self._target_position = target_position
        self._reached = False

    def step(self, current_position: float, current_velocity: float, dt: float) -> tuple[float, float, float]:
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
        distance = self._target_position - current_position
        direction = 1.0 if distance >= 0.0 else -1.0

        if (abs(distance) <= self.position_tolerance and abs(current_velocity <= self.velocity_tolerance)):
            self._reached = True
            return self._target_position, 0.0, 0.0
        
        breake_distance = (current_velocity ** 2) / (2.0 * self.max_acceleration)
        breaking_needed = abs(distance) <= breake_distance + 1e-9 #TODO necessary?? 1e-9?? #TODO replace magic_number

        wrong_direction = (current_velocity * direction) < 0.0

        if breaking_needed or wrong_direction:
            velocity_sign = 1.0 if current_velocity >= 0.0 else -1.0
            target_acceleration = -velocity_sign * self.max_acceleration
        elif abs(current_velocity) < self.max_veloity:
            target_acceleration = direction * self.max_acceleration
        else:
            target_acceleration = 0.0

        target_velocity = current_velocity + target_acceleration * dt
        target_velocity = max(-self.max_veloity, min(self.max_veloity, target_velocity))

        target_position = current_position + target_velocity * dt
        if direction > 0:
            target_position = min(target_position, self._target_position)
        else:
            target_position = max(target_position, self._target_position)

        return target_position, target_velocity, target_acceleration
    
    @property
    def target_position(self) -> float:
        """current set target_position [m]"""
        return self._target_position
    
    @property
    def reached(self) -> bool:
        """True if axis reached the target_position and is not moving"""
        return self._reached
