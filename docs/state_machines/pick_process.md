
## Whats in this Document
**This document explains in breaked down Steps how the Picking Process is going to be realized across the Orcestrating Main Node and the Executin AxisController Node. Therefore it is not particullary a State machine, but described as a Flow across the Programm.**

### Declarations:
[M]: represents the Main-node
[A]: represents the Axis-node

The Main-node sends the NimSortTarget with TargetPoint and process_id to the Axis-node.
The Axis-node sends the feedback with gripper_active and reached

### Steps
General Responsibilitys
**[A]**: sends the currend reached and gripper_active data as minimalistic feedback to the Main Node.
**[M]**: interpret the reached with a edge detector including possible filters as a False threshold until it can rise again.

Flow between nodes:
**[A]**: The Axis has to be in one pick-pre-position either the Generic-pick.pre-position or the Object-pick-pre-position.
**[M]**: The Main has to interpret the received reached as a reached_rise in the corresponding state for the pick_preposition to command a Pick-position which is caluclated from the real Object-position added to a constant distance multiplied by the coveyorbelt speed, so that we have more buffer to pick if the Object moves faster because of the limited X-Axis Hardware Speed.
In this drive we command the ProcessID related to the PickProcess
**[A]**: The Axis receives a new Target with the ProcessID sa Picking Drive.
In this mode the abstract robot-axis has to adapt the reached feedback by ignoring the values of the x-Axis because the axis has to stay in motion in the whole pick-process. 
The PorcessID Picking drive is also interpreted as gripper_active has to be true.
After the Y- and Z- Axis feedbacked reached as normal the reached feedback from the Axis to the Main return as true.
**[M]**: The Main interprets the reached as alwas and continues the PickingDrive after receiving an interpreted reached_rise, with lifting the part of the belt by commanding a new Target with still the Picking ProcessID.
**[A]**: The Axis continues as described and still ignoring the X-Axis in the reached return value.
**[M]**: After the Liftoff is Completed by reveiving a interpreted reached_rise the Main continues with a new Target as Drop point with a ProcessID for normal drive with continues gripper_active as true.
**[A]**: The Axis keeps the girpper_active but includes the X-Axis in reached-return-value agian.