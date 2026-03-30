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

