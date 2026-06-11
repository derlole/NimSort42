# NimSort42
This Repo Contains all the Files and Documentation to run The Nimsort Project which controlls a 3 Axis Portal Robot to pick Objects from a Moving Conveorbelt to sort them accourding to their class into different Containers
To See the Docs see this File: [documentaion.md](documentation/documentation.md)

## Collaborators and responsibility
- Louis Moser
- Yannick Bachhuber
- Benjamin Keppler 

## Pull Submodules
In order to build all packages you have to recursively pull the submodules into your local repository with the following command:
```bash
git submodule update --init --recursive
```
## Build all necessary modules
```bash
cd ros_ws
colcon build
source install/setup.bash
```
Make sure that there are no build errors or build files in the wrong directory, after building you should be able to start everything needed for the application to run.

## Run Submodules
```bash
ros2 launch ro45_ros2_pickrobot_serial launch_nodes.py
```
## Note the remarks from the ro45_ros2_pickrobot_serial package listed below for communicating with the packages:
In case the ESP32 /ESP 8266 is not detected (ttyUSB0 port) this is since the signature of the nodeMCU board clashes with another device. In this case run the command
```bash
sudo apt-get remove -y brltty
```
The user must be in the group dialout to have access to the serial interfaces. This can be checked with the command groups. If dialout is not in the list add your user to this group using the command
```bash
sudo usermod -a -G dialout YOURUSERNAME
```

## Install Global Python dependencies
```txt
opencv-python
rclpy
numpy
joblib
pandas
matplotlib
scipy
pytest
```

## Install Local Python packages
The Repository Contains a python package for easier reference into the files across the repo. This Package can be installed locally with the following commands:
```bash
cd nimsort_logic
pip install -e .
```

## Align the Camera
To see how to start and how to correctly align the Camera see this File: [camera_alignment.md](docs/explanations/camera_alignment.md)

## Run Nodes
See how the Nodes can be run correctly here: [starting_nodes.md](docs/explanations/starting_nodes.md)