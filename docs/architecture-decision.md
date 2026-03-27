# Architecutre responsibilitys

## Ros Nodes

### Vision
- Orcestrate when picture is going to be taken
- Process model-input-data from taken picture with OpenCV
- receive model output from FeatureDetection
- calculate current position of object. (current defines time when image was taken)
- publish NimSortImageDate

### PositionPrediction
- receive NimSortImageData
- publish NimSortPrediction

### MainNode
- receive NimSortPrediction 
- orcestrate Programm Flow
- call system initialization
- publish NimSortTarget

### AxisController
- receive NimSortTarget
- receive RobotPos
- hold and orcestrate all Axis
- know and prevent forbidden zones
- publish RobotCmd

## Python Calsses

### CSTransformation
- providing functions to Transform between CordinateSystems

### OpencvPipeline
- Taking Picture
- process picture with according filters
- calculate an return parameters

### FeatureDetection
- receive parameters
- calculate object clasification with parameters
- calculate object position
- return calculated obejct data

### PositionPrediction
- store received ImageData in any fitting datastructure
- calculate positionPrediction for next possible Object

### MainLogic
- System statemachine

### InitProcess
- initialize System

### Axis
- hold axis data (position, velocity, acceleration)
- calculate acceleration form position

### Controller
- controll acceleration


