## Axis.py

### Example implementation
```py
from controller import Controller
from axis import Axis

ctrl_x = Controller(kp=10.0, kd=2.0, use_derivative_filter=True,
                    filter_coefficient=0.15, max_acceleration=5.0)
axis_x = Axis(name="X", controller=ctrl_x)

# Im ROS-Callback:
accel = axis_x.update(
    current_position=0.42,
    target_position=1.00,
    dt=0.01,
)
```

### Design Decisions
- The Axis class gets a Cotroller by initialization so the Controller can externaly be configured.
- every units are implied as SI-units in EVERY variable
- the update function should be called zyclically to regulate the axis acceleration
- public data are priovided through the `AxisState` class and properties