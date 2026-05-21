# concepts of Software-architecture

The Concept of the General Software Architecture producec a dependency alignment where the nodes in general only have dependencys visually upwards in [SW-arch.drawio](../../misc/arch.drawio). Therefore the Vision Node has no dependency above and the AxisController Node has no dependency below.

In general the only harm for Person or Hardware is produced in the AxisController Node because it is the only node that communicates with the hardware.
But the Axis Controller node depends on the Main node which depends on the PositionPrediction node which depends on the Vision Node.
Also the AxisController node depends on the robot_position data from the serial bridge

# Conceps to establish Fail Safe
For failsafe in the AxisController node we conclude that we have to be in a safe position to shutdwon the AxisController node. As easiest Solution we picked a homing drive, as we do not have to implement something else as the reset and restart of the homing Process.

This process has to be triggerd in all following cases.
- The Vision Node throws an error which can not be handled
- The PostionPrediction node throws an error which can not be handled
- The Main node throws an error which can not be handedld
- The AxisController node throws an error which can not be handled
- The robot_position data are missing

## Simplyfieing
To bring this down to less casees in the AxisController node every dependency from nodes to other nodes are concluded as a Indispensable criterion of existence. So if any data from a dependend node in any node are missing the node cleans up and kills itself. To do not run in any udp package loss and shutdown without an error the grace period of any missing data is 1 second with represents 10 missing data packages.
In general we result in reduces cases. To state the fauilure of the Main node is interpreted as a thrown error in the AxisController which can not be handeld
- The AxisController node throws an error which can not be handled
- The robot_position data are missing

# robot_position_data
As the robot_position data is far more critical than the other node dependecys to the AxisController the concepts are handled the same, like shuting down the AxisController if the data are misisng, but with a shorter grace period of 0.5 seconds.

# pre_shutdown_sequence
To establish to not drive any crashes while killing the AxisController. The AxisController reexecutes the init-logic and bypassing the Axis Classes. This leads to safe accelerations into the as home defined endstops.
After the acceleration publishes the AxisController node can die but in the best case the node survieves until the homing is done and kills itself after.