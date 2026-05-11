## This document explains in breaked down Steps how the Picking Process is going to be realized across the Orcestrating Main Node and the Executin AxisController Node

### Declarations:
[M]: represents the Main-node
[A]: represents the Axis-node

The Main-node sends the NimSortTarget with TargetPoint and process_id to the Axis-node.
The Axis-node sends the feedback with gripper_active and reached

### Steps
[M]: sends the pick-preposition
[A]: goes to commanded (pick-pre)position
[M]: wait for reached
[A]: sends reached when reached
[M]: sends dummy values until the actuall picking process can be started
[M]: sends current point of the objec twith a process_id, representing the poick process
[A]: accelerates up to the conveyorbelt_speed with activated gripper and automatically drives down onto the belt and up again.
[M]: wait for reached, which represents the end of driving up after pick
[A]: goes back to point-controlled not speed controlled