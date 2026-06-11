### Starting and unsing Camera Node
#### Parameter
camera_index: default 4

starting as following to run with camera_index 4 as default
```bash
ros2 run nimsort_nodes nimsort_vision
```
Starting as following to use any camera indexs as integer

```bash
ros2 run nimsort_nodes nimsort_vision --ros-args  -p camera_index:=2
```
When does the Node Stops?
Either when you press Ctrl+C in the Terminal or the Implemented Fail-Save Concept leads to a self kill of the Node.

### Starting and unsing PositionPrediction Node

starting as following to run PositionPredictionNode
```bash
ros2 run nimsort_nodes nimsort_position_prediction
```

When does the Node Stops?
Either when you press Ctrl+C in the Terminal or the Implemented Fail-Save Concept leads to a self kill of the Node.

### Starting and unsing Main Node

starting as following to MainNode
```bash
ros2 run nimsort_nodes nimsort_main
```

When does the Node Stops?
Either when you press Ctrl+C in the Terminal or the Implemented Fail-Save Concept leads to a self kill of the Node.

### Starting and unsing PositionPrediction Node

starting as following to run AxisControllerNode
```bash
ros2 run nimsort_nodes nimsort_axis_controller
```

When does the Node Stops?
Either when you press Ctrl+C in the Terminal or the Implemented Fail-Save Concept leads to a self kill of the Node.