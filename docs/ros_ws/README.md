# ROS2 Workspace – Überblick

## Willkommen! 👋
Der `ros_ws` Ordner enthält die ROS2-Integration für NimSort42. Hier laufen die verschiedenen Knoten (Nodes) die mit dem nimsort_logic Modul kommunizieren.

## Pakete im Workspace

### 1. [nimsort_msgs](NIMSORT_MSGS.md) – Nachrichtenschnittstellen
Custom ROS2 Message-Typen für die NimSort-Kommunikation zwischen Nodes.

**Nachrichten:**
- `NimSortTarget` – Zielposition für Roboter
- `NimSortPrediction` – Prognostizierte Objektposition
- `NimSortMotionState` – Status der Roboterbewegung
- `NimSortImageData` – Erkannte Objekt-Daten
- `NimSortConveyorbeltSpeed` – Förderband-Geschwindigkeit

---

### 2. [nimsort_nodes](NIMSORT_NODES.md) – Hauptknoten
ROS2 Nodes die die eigentliche Logik ausführen.

**Wichtigste Nodes:**
- `MainNode` – Zentrale State Machine (nimsort_main mit ROS2 Wrapper)
- `AxisControllerNode` – Roboterbewegung/Achsenkontrolle
- `VisionNode` – Bildverarbeitung und Objekterkennung
- `PositionPredictionNode` – Position-Prognose für Objekte

