# Logging convetions in NimSort Nodes and Python Classes

## Information Log
### Nodes
get_logger().info(CONTENT)

### Raw Python Code
print([INFO]: CONTENT)

## Warning Log
### Nodes
get_logger().warning(CONTENT)

### Raw Python Code
print([WARN]: CONTENT)

## Error Log
### Nodes
get_logger().error(CONTENT)

### Raw Python Code
print([ERR-]: CONTENT)

## Info
when launching nodes with launch file the node-name is automatically setup in front, so we do not need to add them manually to the log-message

## Content definition

CONTENT:
[ClassShortName][functionName]: msg

## Length
By defining length con ClassShortName and functionName the logs stay viewable, due to obvious start of the message.

Therefore the ClassShortName has to be 4 Characters long. e.g for the class AxisController the ClassShortName could be -> [AxCo] or [AC--] 

Same concept for functionNames but with 8 Characters. 
e.g. for the update function -> [update--]

lets pretend the ValueError in line 74 in the class Axis happens the log without launch file would look like this:
[ERR-]: [Axis][update--]: Axis 'X': dt must be positive -10.0

print(f"[PoPr][ROOT----][INFO]: Objekt {object_type} hat Schwellwert erreicht – wird entfernt.") 