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

- `init_cv()` Inits the OpencvPipeline system
- `capture_image()` Captures an Image
- `get_position()` Get the Position in Cam-CS #TODO Maybe in World
- `get_timestamp()` Get the Timestamp
- `rest_cv()` Resets the whole Process

#TODO KOMMENTAR: evlt. diese funktionen im Interface nur als eine funktion (oder höchstens zwei) z.B. capture_image() und get_image_data() oder sowas. was intern passiert muss/soll im interface nicht zu sehen sein. init_cv brachst du nicht jede klasse hat zwangsweise eine __init__() function


### FeatureDetection

- `init_feature_Detection()` Inits the FeatureDetection System
- `set_image()` Set the Image
- `get_feature()` Get the feature #TODO Maybe other word for feature (objekt)
- `reset_feature_Detection()` Resets the whole Process

#TODO KOMMENTAR: init_bla wieder löschen, braucht man nicht im interface. auch hier set_image() und get_feature() kombinieren, das bild und das feature sind keine speziellen attribute der Klasse, diese müssen nicht mit gettern und settern abstrahiert werden, desewegen wollen wi von außen so einfache zugriffe wior möglich. du kannst, wenn du das möchtest soetwas, wie propertys für get_last_feature_data machen, wo erneut der letzte datensatz wieder kommt, aber das ist optional.

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