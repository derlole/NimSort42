# Architecture responsibility's

## Ros Nodes

### Vision
- Orchestrate when picture is going to be taken
- Process model-input-data from taken picture with OpenCV
- receive model output from FeatureDetection
- calculate current position of object. (current defines time when image was taken)
- publish NimSortImageDate

### PositionPrediction
- receive NimSortImageData
- publish NimSortPrediction

### MainNode
- receive NimSortPrediction 
- orchestrate Programm Flow
- call system initialization
- publish NimSortTarget

### AxisController
- receive NimSortTarget
- receive RobotPos
- hold and orchestrate all Axis
- know and prevent forbidden zones
- publish RobotCmd

## Python Classes

### CSTransformation
- providing functions to Transform between CoordinateSystems

### OpenCVPipeline
- Taking Picture
- process picture with according filters
- calculates object position
- calculate an return preprocessed Image and Object position

### FeatureDetection
- receive preprocessed Image 
- retrieves needed parameters
- calculate object classification with parameters
- return calculated object data

### PositionPrediction
- store received ImageData in any fitting data structure
- calculate positionPrediction for next possible MagicObject

### MainLogic
- System state machine

### InitProcess
- initialize System

### Axis
- hold axis data (position, velocity, acceleration)
- calculate acceleration form position
- calculate in the RCS (RobotCoordinateSystem)

### Controller
- control acceleration


