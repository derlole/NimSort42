## MSG

### NimSortImageData.msg

geometry_msg/msg/Point current_position_wcs  
int32 object_type --> cat [0], magicalUnicorn [1], square [2], circle [3] 
int32 ts --> timestamp  


### NimSortPrediction.msg

geometry_msg/msg/Point predicted_position_wcs  
int32 object_type --> cat [0], magicalUnicorn [1], square [2], circle [3]  


### NimSortTarget.msg

geometry_msg/msg/Point target_point    
int32 process_id --> represents Axistask #TODO genau definieren!!  


### NimSortMotionState.msg

bool reached  
bool gripper_active  


## Python Interfaces

### OpencvPipeline
This interface defines the interaction between the Vision node and the FeatureDetection.

- `capture_image()` Captures an Image
- `get_image_data() -> tuple[float, float, np.ndarray]` Get the Data from the Image (Position in X and Y in Camera CS, The Image)
- `get_ image_data() -> tuple[float, float, np.ndarray]` Get the Data from the Image (Position in X and Y in Camera CS, The Image)

### FeatureDetection

- `get_feature(image: np.ndarray) -> int` Get the Feature (magic Unicorn, Cat, Circle and Square)

### PositionPrediction
This interface defines the interaction between the PositionPredictionNode and the corresponding python logic.

- `set_conveyor_belt_speed(speed_mps)` sets the handed Conveyorbelt Speed for position prediction in logic
- `set_object_data(object_type, position, ts)` stores the data in a corresponding datastructure for detected and handed Objects.
- `calculate_next_object_position() -> tuple[float, float, float]` returns the current position of the next tecnically grippable Object in the WCS
- properties to see what values are stored in the datastructure and the conveyorbelt Speed.

### Main
This interface defines the interaction between the MainNode and the corresponding logic

- `process_motion_state()` handles the current motion state
- `process_prediction()` handles the new PositionPrediction values
- `get_current_state()` gets the current main state
- `reset()` resets the main_logic
### AxisInterface
This interface defines the interaction between the AxisController node and the individual axis instances.

- `set_target()` defines the target position the axis should move to  
- `update()` calculates the current output values (e.g. for the RobotCmd message) based on the internal state  
- properties provide access to important axis information (e.g. current position, velocity, etc.)  
- `get_state()` returns a snapshot of the axis state containing all relevant information at the time of the call  


### ControllerInterface
This interface defines a minimal structure for controllers to process input values and produce an output.

- `compute()` calculates the controlled output value based on the given input values  
- properties define the required inputs and resulting outputs of the controller  

### TrajectoryPlanerInterface
This interface defines two impoirtant functions
- `the set_target()` to define a target to which one should be traveld
- `step()` calculates the values which would be necessary to stay on the trajectory for the last given target
- two porpertys to get the last given target_position and reached to check wether the last given point is reached.