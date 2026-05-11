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
