# nimsort_nodes – ROS2 Knoten-Implementation

## Überblick
Das `nimsort_nodes` Paket enthält alle ROS2 Nodes (Python-basiert). Jeder Node wrappet die Logik aus `nimsort_logic` und kommuniziert über ROS2 Topics mit anderen Nodes.

## Hauptknoten

### MainNode (`main_node.py`)
**Zentrale State Machine für Sortierlogik – ROS2 Wrapper**

Wrappet: `nimsort_main.NimSortMain` (aus nimsort_logic)

**Subscriptions:**
- `/NimSortMotionState` – Bewegungs-Feedback vom AxisController
- `/NimSortPrediction` – Prognostizierte Objektposition

**Publications:**
- `/NimSortTarget` – Zielposition für Roboter
- `/NimSortPredictionFeedback` – Boolean: ob Prediction gültig ist

**Wichtige Methoden:**
- `listener_callback_motion()` – Aktualisiert Motion-Status
- `listener_callback_prediction()` – Verarbeitet Prediction + sendet Feedback
- `main_order()` – Hauptschleife (10 Hz Timer)

**Logik:**
1. Empfange Prediction von PositionPredictionNode
2. Prüfe ob Position plausibel/erreichbar ist
3. Sende Feedback (valid/invalid)
4. Falls valid → sende NimSortTarget an AxisController

---

### AxisControllerNode (`axis_controller_node.py`)
**Roboterbewegung und Achsenkontrolle**

Wrappet: `nimsort_motion.axis.Axis` (aus nimsort_logic)

**Subscriptions:**
- `/NimSortTarget` – Zielposition vom MainNode
- `robot_position` – Aktuelle Position vom Roboter

**Publications:**
- `/NimSortMotionState` – Bewegungs-Status (reached, gripper_active)
- `robot_commands` – ROS-Commands an Roboter-Hardware

**Wichtige Methoden:**
- `nimsort_target_callback()` – Zielposition empfangen
- `robot_pos_callback()` – Aktuellen Status vom Roboter empfangen
- `main_order()` – Verarbeitet Target + sendet Commands

**Besonderheiten:**
- **Timeouts:** 1.0s für Target, 0.5s für RobotPos (Fehler bei Timeout)
- **InitProcess:** Kalibrierungs-Sequenz beim Start
- **Offset-Tracking:** XYZ-Offsets für Positionsanpassung

---

### VisionNode (`camera_supreme_commander.py`)
**Bildverarbeitung und Objekterkennung**

Wrappet: 
- `nimsort_vision.OpencvPipeline` 
- `nimsort_vision.ConveyorSpeedEstimator`
- `nimsort_feature_detection.FeatureDetection`

**Publications:**
- `/NimSortImageData` – Erkannte Objektposition + Typ
- `/NimSortConveyorbeltSpeed` – Förderband-Geschwindigkeit

**Parameter:**
- `camera_index` – Kamera-Nummer (default: 4)

**Logik:**
1. Erfasse Kamerabild
2. Führe OpenCV-Pipeline aus → erkannte Positionen
3. Klassifiziere Objekte (Feature Detection)
4. Schätze Förderband-Geschwindigkeit
5. Publiziere beide Topics

**Fehlerbehandlung:**
- RuntimeError bei Kamera-Initialisierung → log & re-raise
- Kamerafehler während Laufzeit → skip frame

---

### PositionPredictionNode (`position_prediction_node.py`)
**Position-Prognose für Objekte**

Wrappet: `nimsort_vision.position_prediction_logic.PositionPrediction`

**Subscriptions:**
- `/NimSortImageData` – Erkannte Positionen von Vision
- `/NimSortConveyorbeltSpeed` – Förderband-Geschwindigkeit
- `/NimSortPredictionFeedback` – Feedback vom MainNode (valid/invalid)

**Publications:**
- `/NimSortPrediction` – Extrapolierte Objektposition

**Logik:**
1. Empfange Objektposition von Vision
2. Empfange Förderband-Geschwindigkeit
3. Extrapoliere Position basierend auf Geschwindigkeit
4. Sende Prediction
5. Je nach Feedback (MainNode): Track Position oder discard

**Timeout:**
- 1.0s ohne neue ImageData → stoppe Prediction

---

### ManualAxisNode (`manual_axis.py`)
**Manuelle Achsen-Steuerung (für Debugging/Setup)**

Erlaubt manuelle X/Y/Z-Bewegungen für Kalibrierung und Fehlersuche.

---

## Node-Abhängigkeiten (Start-Reihenfolge)

```
VisionNode (unabhängig)
   ↓
PositionPredictionNode (benötigt Vision Output)
   ↓
MainNode (benötigt Prediction)
   ↓
AxisControllerNode (benötigt MainNode Targets)
```

## Threading & Callbacks

**Multi-Threaded Executor** ermöglicht parallele Callback-Ausführung:
- Vision kann während MainNode läuft neue Bilder verarbeiten
- Keine Blockierung zwischen Nodes

**MutuallyExclusiveCallbackGroup** schützt shared State:
- Z.B. in AxisControllerNode: `main_order()` und `robot_pos_callback()` laufen nicht gleichzeitig

## Configuration & Parameter

Alle Parameter kommen aus `configs/`:
- `config_main.py` – Positionen, Grenzen
- `config_axis.py` – Achsen-Parameter
- `config_camera.py` – Vision-Parameter
- `config_position_prediction.py` – Prognose-Parameter


## Logging

Alle Nodes verwenden ROS2 Logger:
```python
self.get_logger().info("Message")
self.get_logger().error("[ERROR_CODE] Details")
```

## Fehlerbehandlung

- **Timeout:** Wenn Node lange keine Messages erhält → log warning
- **Invalid Position:** MainNode sendet Feedback=False → PositionPrediction verwirft
- **Hardware Error:** AxisController kriegt keine RobotPos → error & stop

---

## Integration mit nimsort_logic

Alle Nodes nutzen direkt die Python-Klassen:

```python
# MainNode
from nimsort_main.main_logic import NimSortMain
self.nimsort_main = NimSortMain()

# VisionNode
from nimsort_vision.opencv_pipeline import OpencvPipeline
self.pipeline = OpencvPipeline(camera_index)

# PositionPredictionNode
from nimsort_vision.position_prediction_logic import PositionPrediction
self.logic = PositionPrediction()
```

Die Nodes sind **Wrapper**, nicht Neu-Implementierung!

---

## Debugging & Testing

**Starten Sie einzelne Nodes:**
```bash
# Nur Vision
ros2 run nimsort_nodes camera_supreme_commander

# Nur Prediction
ros2 run nimsort_nodes postion_prediction_node

# Nur Main
ros2 run nimsort_nodes main_node

# Nur AxisController
ros2 run nimsort_nodes axis_controller_node
```
