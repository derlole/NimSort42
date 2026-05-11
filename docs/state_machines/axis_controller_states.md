## This Documentation File explains the meanings and state changes of the AxisControllerNode

### 1. Empy
The Empty state does represent the initial state of the AxisControllerNode. It repreesnts the Software-Emptyness of the AxisControllerNode, because the class atributes axis_x ,_y, _z are empty. This represents the uninitialized state of the AxisControllerNode
This state can be left due calling an initialization process from the /NimSortTarget topic the following state is always the INITIALIZING_AXIS_HW

### 2. INITIALIZING_AXIS_HW
This state represents the goal initialize the Axis in an hardware perspective. This means an homing process. In this state the AxisController node calls the initialization process logik cyclyc. It provides the Position values in raw values and recieves the acceleration values for accerleration up to an homing speed.
This state can be left due to an field finished from the initialization logic. This filed represents the finalization of the hardware homing drive. The next state is always the INITIALIZING_AXIS_SW

### 3. INITIALIZING_AXIS_SW
This state is just for initialization of the Axis Objects with its controllers and TrajectoryPlanners. The Constants for the Values are passed with the init Process of the Objects. resulting are not Empty -> filled axis atrributes in the AxisControllerNode. This state always results in the RUNNING state.

### 4. RUNNING
This state represents an initialized and ready state of the AxisControllerNode. at this the Axis-attributes cannot be None therefore points can be given to any axis. The axis handles the logic of TrajectoryPlanning and Controlling by revieving the position in RobotCoordinateSystem and providing accelerations for the axis. This State is only left if fo 3 seconds no NimsortTarget is received.

### 5. RETURNING_HOME
This state handels an safe init drive after the RUNNING step is left due to missing NimsortTarget values. It calls the Init-proccess exactly the same as the `INITIALIZING_AXIS_HW` state after resetting and starting it again.
This state is left after the self.init_process states finish.

### 6. SHUTDOWN
This State handles the Shudown of the Node by throwing an RunntimeError.