# NimSort42

## Pull Submodules
```bash
 git submodule update --init --recursive
```

## Run Submodules
```bash
ros2 launch ro45_ros2_pickrobot_serial launch_nodes.py
```
## Note the remarks from the ro45_ros2_pickrobot_serial packate listed below for communicating with the packages:
In case the ESP32 /ESP 8266 is not detected (ttyUSB0 port) this is since the signature of the nodeMCU board clashes with another device. In this case run the command
```bash
sudo apt-get remove -y brltty
```
The user must be in the group dialout to have access to the serial interfaces. This can be checked with the command groups. If dialout is not in the list add your user to this group using the command
```bash
sudo usermod -a -G dialout YOURUSERNAME
```

## Install Local Python packages
The Repository Contains a python package for easier reference into the files across the repo. This Package can be installed locally with the following commands:
```bash
cd nimsort_logic
pip install -e .
```

## Other md Files
- CSSystems.md contains the CordinateSystems which are classified for this Porject [CSSystems.md](docs/CSSystem.md)
- main.md contains the main Software documentation [main.md](docs/main.md)
- projektplanung.md contains the Project Planning phase decisions and Information which are not specified in the Github Project [projektplanung.md](docs/projektplanung.md)
- arcitecture-decisions.md contains the requirements for the single architecutre pieces [architecture-decisicions.ms](docs/architecture-decision.md)
- logging.md contains the logging convetion across the ros2 and python scripts across this repo to have better readable logs [logging.md](docs/logging.md)
- interfaces.md contains the documentation for the decisions on each interfaces, the ros2 msgs aswell as the interfaces between raw python code and ros2 nodes. [interfaces.md](docs/interface.md)