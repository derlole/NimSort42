### Starting and using the Camera node
#### Parameter
`camera_index` (default: 4)

Start (default camera index 4):
```bash
ros2 run nimsort_nodes nimsort_vision
```
Start with explicit camera index:
```bash
ros2 run nimsort_nodes nimsort_vision --ros-args -p camera_index:=2
```
When does the node stop?
Either when you press Ctrl+C or when the implemented failsafe causes the node to terminate.

### Starting the PositionPrediction node

Start:
```bash
ros2 run nimsort_nodes nimsort_position_prediction
```

When does the node stop?
Either when you press Ctrl+C or when the implemented failsafe causes the node to terminate.

### Starting the Main node

Start:
```bash
ros2 run nimsort_nodes nimsort_main
```

When does the node stop?
Either when you press Ctrl+C or when the implemented failsafe causes the node to terminate.

### Starting the AxisController node

Start:
```bash
ros2 run nimsort_nodes nimsort_axis_controller
```

When does the node stop?
Either when you press Ctrl+C or when the implemented failsafe causes the node to terminate.