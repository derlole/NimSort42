"""
test_axis.py
---
Unit tests for Axis class.
"""

import pytest
from nimsort_motion.axis import Axis
from nimsort_motion.controller import Controller
from nimsort_motion.trajectroy_planner import TrajectoryPlanner

class TestAxis:
    def setup_method(self):
        self.planner = TrajectoryPlanner(max_velocity=1.0, max_acceleration=1.0)
        self.controller = Controller(kp=1.0, kd=0.0, output_limit=10.0)
        self.axis = Axis("Test", self.controller, self.planner, 0.0)

    def test_init(self):
        assert self.axis.position == 0.0
        assert self.axis.velocity == 0.0
        assert self.axis.acceleration == 0.0

    def test_set_target(self):
        self.axis.set_target(5.0)
        assert self.axis._target_position == 5.0

    def test_update(self):
        self.axis.set_target(1.0)
        accel = self.axis.update(0.0, 0.1)
        assert isinstance(accel, float)

    def test_update_invalid_dt(self):
        with pytest.raises(ValueError):
            self.axis.update(0.0, 0.0)

    def test_reset(self):
        self.axis.set_target(1.0)
        self.axis.update(0.5, 0.1)
        self.axis.reset()
        assert self.axis.position == 0.0
        assert self.axis.velocity == 0.0

    def test_get_state(self):
        state = self.axis.get_state()
        assert state.position == 0.0
        assert state.velocity == 0.0

    def test_repr(self):
        repr_str = repr(self.axis)
        assert "Test" in repr_str