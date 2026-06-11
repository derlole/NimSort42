# nimsort_nodes – ROS2 Knoten-Implementation

## Überblick
Das `nimsort_nodes` Paket enthält alle ROS2 Nodes (Python-basiert). Jeder Node wrappet die Logik aus `nimsort_logic` und kommuniziert über ROS2 Topics mit anderen Nodes. 
Alle Topics sind entweder default ROS2 Typen, oder durch [nimsort_msgs.md](nimsort_msgs.md) dokumentiert.


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

**Zyklischer Hauptablauf:**
- 

**Timeout:**
- 1.0s ohne neue Prediction → stoppe Node

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

**Zyklischer Hauptablauf:**
- 


**Besonderheiten:**
- **Timeouts:** 1.0s für Target, 0.5s für RobotPos (Fehler bei Timeout)
- **InitProcess:** Kalibrierungs-Sequenz beim Start
- **RescueInit:** Falls Kommunikation zu anderen Nodes fehlschlägt

**Timeout:**
- 1.0s ohne neue Target → stoppe Achse nach `RescueInit`

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

**Wichtige Methoden:**
- 

**Zyklischer Hauptablauf:**
- 


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

**Wichtige Methoden:**
- 

**Zyklischer Hauptablauf:**
- 


**Timeout:**
- 1.0s ohne neue ImageData → stoppe Prediction

---

### ManualAxisNode (`manual_axis.py`)
**Manuelle Achsen-Steuerung (für Debugging/Setup)**

- Erlaubt manuelle X/Y/Z-Bewegungen für Kalibrierung und Fehlersuche.
- Implementiert den Regler, und Achsendsoftware, welche auch im echten System verwendet wird.

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
Alle Potentiellen Feedbacks sind nicht unbedingt Notwendig für das Überleben der Node

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
self.get_logger().info("CONTENT")
self.get_logger().error("CONTENT")
```

Der Content ist so gecshrieben, dass das Gesamtbild des Logs den Logging Konventionen, die in [logging.md](../sw_planning/logging.md) beschrieben sind.

## Integration mit nimsort_logic

Alle Nodes nutzen direkt die zugehörigen Python-Klassen, wie in [nimsort_logic.md](../../documentation/nimsort_logic.md) beschrieben

Die Nodes sind **Wrapper** dieser Logik, nicht Neu-Implementierung, damit ncah bedarf möglichst einfach auf eine andere Middleware gewechselt werden kann.

