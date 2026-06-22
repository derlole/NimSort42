
## What's in this document
This document describes, step by step, how the picking process is realized between the orchestrating Main node and the executing AxisController node. It is written as a process flow rather than a strict state machine.

### Declarations
- `[M]` — Main node
- `[A]` — Axis node

The Main node sends a `NimSortTarget` (target point + `process_id`) to the Axis node. The Axis node sends feedback containing `gripper_active` and `reached`.

### Steps — responsibilities and flow

General responsibilities
- **[A]**: Send minimal feedback to the Main node: `reached` and `gripper_active`.
- **[M]**: Interpret `reached` using an edge detector (and optional filters) to detect a rising edge reliably.

Flow between nodes
- **[A]**: Axis must be in a pick pre-position (either a generic pick pre-position or an object-specific pick pre-position).
- **[M]**: Main detects a `reached_rise` for the pick pre-position and commands a pick position. The pick position is calculated from the measured object position plus a safety offset that compensates for the conveyor belt speed (to provide buffer when the object moves).
- **[M]**: The Main sends a target with the ProcessID for the picking drive.
- **[A]**: On receiving a picking ProcessID, the Axis adapts the `reached` feedback: the X-axis values are ignored because the axis must remain in motion during the pick process. The ProcessID implies `gripper_active == true`.
- After Y and Z report `reached` normally, the Axis reports `reached = true` to the Main.
- **[M]**: Main interprets the `reached` (via `reached_rise`) and continues the picking drive, e.g., lifting the object by commanding a new target with the same picking ProcessID.
- **[A]**: Axis continues, still ignoring X in the `reached` evaluation.
- **[M]**: After liftoff is completed (interpreted `reached_rise`), Main commands a drop point with a ProcessID for normal drive while keeping `gripper_active = true`.
- **[A]**: Axis keeps `gripper_active` and — after the drop drive begins — includes X again in the `reached` evaluation.