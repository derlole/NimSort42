"""
test_trajectory_planner.py
---
Unit tests for TrajectoryPlanner class.
"""

import pytest
from nimsort_motion.trajectroy_planner import TrajectoryPlanner

class TestTrajectoryPlanner:
    def test_init_valid(self):
        planner = TrajectoryPlanner(max_velocity=1.0, max_acceleration=2.0)
        assert planner.max_velocity == 1.0
        assert planner.max_acceleration == 2.0
        assert planner.reached == False  # Initial False now

    def test_init_invalid_velocity(self):
        with pytest.raises(ValueError):
            TrajectoryPlanner(max_velocity=0.0, max_acceleration=1.0)

    def test_init_invalid_acceleration(self):
        with pytest.raises(ValueError):
            TrajectoryPlanner(max_velocity=1.0, max_acceleration=-1.0)

    def test_compute_accelerate(self):
        planner = TrajectoryPlanner(max_velocity=1.0, max_acceleration=1.0)
        acc = planner.compute(target_position=10.0, current_position=0.0, current_velocity=0.0)
        assert acc == 1.0  # Richtung positiv, beschleunigen
        assert planner.reached == False

    def test_compute_brake(self):
        planner = TrajectoryPlanner(max_velocity=1.0, max_acceleration=1.0)
        acc = planner.compute(target_position=0.1, current_position=0.0, current_velocity=0.5)
        # Brake distance = (0.5^2)/(2*1) = 0.125, distance=0.1 < 0.125, so brake
        assert acc == -1.0
        assert planner.reached == False

    def test_compute_wrong_direction(self):
        planner = TrajectoryPlanner(max_velocity=1.0, max_acceleration=1.0)
        acc = planner.compute(target_position=0.0, current_position=1.0, current_velocity=0.5)
        # Wrong direction, brake
        assert acc == -1.0
        assert planner.reached == False

    def test_reached(self):
        planner = TrajectoryPlanner(max_velocity=1.0, max_acceleration=1.0)
        acc = planner.compute(target_position=0.0, current_position=0.00005, current_velocity=0.0005)
        assert planner.reached == True