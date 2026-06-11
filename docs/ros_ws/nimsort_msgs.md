# nimsort_msgs – ROS2 Message-Definitionen

## Überblick
Das `nimsort_msgs` Paket definiert alle Custom Message-Typen für die NimSort-Kommunikation zwischen ROS2 Nodes. Es ist ein **Interface-Paket** (CMake-basiert) und stellt die Message-Definitionen bereit.

## Message-Typen

### NimSortTarget
**Zielposition für den Roboter**
```
geometry_msgs/Point target_point
int32 process_id
```

**Erklärung:**
- `target_point` – [x, y, z] Zielkoordinaten im World-Koordinatensystem [m]
- `process_id` – Eindeutige ID des Fahrprozesses

**Verwendet von:** `MainNode` → `AxisControllerNode`

---

### NimSortPrediction
**Prognostizierte Objektposition und Typ**
```
geometry_msgs/Point predicted_position_wcs
int32 object_type
```

**Erklärung:**
- `predicted_position_wcs` – [x, y, z] Vorhergesagte Position des Objekts [m]
- `object_type` – Klassifikations-Typ (z.B. 0=Katze, 1=Einhorn, 3=andere)

**Verwendet von:** `PositionPredictionNode` → `MainNode`

---

### NimSortMotionState
**Status der Roboterbewegung**
```
bool reached
bool gripper_active
```

**Erklärung:**
- `reached` – True wenn Zielposition erreicht wurde
- `gripper_active` – True wenn Greifer aktuell aktiv ist

**Verwendet von:** `AxisControllerNode` → `MainNode` (Feedback)

---

### NimSortImageData
**Erkannte Objekt-Daten aus Bildverarbeitung**
```
geometry_msgs/Point current_position_wcs
int32 object_type
int64 ts
```

**Erklärung:**
- `current_position_wcs` – [x, y, z] Erkannte Position des Objekts im World-CS [m]
  - `-1.0` bedeutet: kein gültiges Objekt erkannt
- `object_type` – Klassifikations-Typ (z.B. 0=Katze, 1=Einhorn, 3=andere)
- `ts` – Zeitstempel [Millisekunden seit Epoche]

**Verwendet von:** `VisionNode` → `PositionPredictionNode`

---

### NimSortConveyorbeltSpeed
**Geschwindigkeit des Förderbands**
```
float64 conveyorbelt_speed
```

**Erklärung:**
- `conveyorbelt_speed` – Aktuelle Geschwindigkeit [m/s]

**Verwendet von:** `VisionNode` → `PositionPredictionNode` und `VisionNode` → `MainNode` 

---

## Integration mit nimsort_logic

Diese Messages sind ROS2-Wrapper um die Python-Datenstrukturen aus `nimsort_logic`:

| Message | Python-Equivalent |
|---------|-------------------|
| `NimSortTarget` | Position-Tuple + ProcessId |
| `NimSortPrediction` | Position + object_type |
| `NimSortMotionState` | `set_motion_state(reached, gripper_active)` |
| `NimSortImageData` | Vision Output (Position + Type) |
| `NimSortConveyorbeltSpeed` | `ConveyorSpeed.get_speed()` |


## Kompilierung

Messages werden beim Build automatisch generiert:
```bash
cd ros_ws
colcon build --packages-select nimsort_msgs
```

Die generierten Python-Klassen sind dann verfügbar:
```python
from nimsort_msgs.msg import NimSortTarget, NimSortPrediction #, usw.
```

## Debugging

Messages im Terminal anschauen:
```bash
# Alle NimSortPrediction Messages
ros2 topic echo /NimSortPrediction

# Mit Type-Informationen
ros2 topic info /NimSortTarget -v

# Message-Definition anzeigen
ros2 interface show nimsort_msgs/msg/NimSortTarget
```
