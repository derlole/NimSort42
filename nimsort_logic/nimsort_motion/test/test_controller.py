"""
test_controller.py
---
Unit tests for Controller class.
"""

import pytest
from nimsort_motion.controller import Controller

class TestController:
    def test_init(self):
        ctrl = Controller(kp=1.0, kd=0.5, output_limit=10.0, kff=0.1)
        assert ctrl.kp == 1.0
        assert ctrl.kd == 0.5
        assert ctrl.kff == 0.1

    def test_compute_basic(self):
        ctrl = Controller(kp=1.0, kd=0.0, output_limit=10.0)
        output = ctrl.compute(error=1.0, dt=0.1)
        assert abs(output - 1.0) < 0.1  # P only, approx

    def test_compute_with_d(self):
        ctrl = Controller(kp=1.0, kd=1.0, output_limit=10.0)
        # First call
        output1 = ctrl.compute(error=1.0, dt=0.1)
        # Second call with same error, velocity should be 0
        output2 = ctrl.compute(error=1.0, dt=0.1)
        assert abs(output2 - 1.0) < 0.1  # D component approx 0

    def test_clamp(self):
        ctrl = Controller(kp=10.0, kd=0.0, output_limit=5.0)
        output = ctrl.compute(error=1.0, dt=0.1)
        assert output == 5.0  # Clamped

    def test_feedforward(self):
        ctrl = Controller(kp=0.0, kd=0.0, output_limit=10.0, kff=1.0)
        output = ctrl.compute(error=0.0, dt=0.1, accel_ff=2.0)
        assert output == 2.0

    def test_reset(self):
        ctrl = Controller(kp=1.0, kd=1.0, output_limit=10.0)
        ctrl.compute(error=1.0, dt=0.1)
        ctrl.reset()
        # After reset, should behave as initial