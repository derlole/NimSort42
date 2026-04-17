# NimSort42 - Code Dokumentation

## Einleitung

NimSort42 ist ein ROS2-basiertes System zur automatisierten Sortierung von Objekten mittels Robotik und Computer Vision. Das System besteht aus drei Hauptkomponenten: Vision (Objekterkennung), Main (Logik und Koordination) und Motion (Bewegungssteuerung).

Diese Dokumentation bietet einen Überblick über die Architektur, Komponenten und die Verwendung des Systems.

---

## How to Use

### Voraussetzungen
- ROS2 (Humble )
- Python 3.10+
- Erforderliche Dependencies: `colcon`, `pytest`

### Installation und Setup

```bash
# Repository klonen
cd /home/yb/ROPRO3/NimSort42
git clone <repo> .

# ROS2 Workspace aufbauen
cd ros_ws
colcon build

# Environment sourcing
source install/setup.bash
```

### Starten des Systems

```bash
# Alle Nodes starten
ros2 launch nimsort_nodes nimsort_launch.py

# Einzelne Nodes starten
ros2 run nimsort_nodes position_prediction_node
```

### Tests ausführen

```bash
# Alle Tests
python3 -m pytest ros_ws/src/nimsort_nodes/test/ -v

# Spezifischer Test
python3 -m pytest ros_ws/src/nimsort_nodes/test/test_Postion_predicton_logik.py -v
```

---

## 1. Vision Module

### Übersicht
Das Vision Module ist verantwortlich für die Objekterkennung und -lokalisierung mittels Computer Vision.

### Komponenten

#### `MagicObject` (`magic_object.py`)
Datenstruktur für erkannte Objekte.


@dataclass
class MagicObject:
    object_type: int                      # Typ des erkannten Objekts
    position: tuple[float, float, float]  # Position (X, Y, Z) in m
    ts: float                             # Zeitstempel der Erkennung
    speed: float = 1.0                    # Objekt-Geschwindigkeit in m/s


#### `PositionPredictionLogic` (`position_prediction_logic.py`)
Hauptlogik zur Positionsvorhersage von Objekten auf dem Förderband.

**Wichtige Methoden:**

| Methode | Beschreibung |
|---------|-------------|
| `set_object_data()` | Speichert erkannte Objekte |
| `set_conveyor_belt_speed()` | Setzt Förderbandgeschwindigkeit |
| `calculate_next_object_position()` | Berechnet nächstes zu sortierendes Objekt |
| `get_next_object_to_publish()` | Gibt Objekt mit höchster X-Position zurück |
| `_update_positions()` | Aktualisiert Positionen basierend auf Zeit |
| `_remove_objects_over_threshold()` | Entfernt Objekte, die den Schwellwert überschreiten |

**Workflow:**
1. Objekte werden via `set_object_data()` hinzugefügt
2. Bei jedem Timer-Call wird `calculate_next_object_position()` aufgerufen
3. Positionen werden erhöht (`_update_positions`)
4. Objekte über Schwellwert (X ≥ 40.0m) werden entfernt
5. Objekt mit höchster X-Position wird publiziert

### Datenstrukturen
Die Daten der Vision werde in die Dataclass Magic Objekt klassifiziert und dann in ein Dictinary abgelegt. Mit dieser Struktur lässt sich über die viel Zahl der Objekte itrieren und somit an das Topic gepublisht werden. 

### Tests

Siehe [test_Postion_predicton_logik.py](../ros_ws/src/nimsort_nodes/test/test_Postion_predicton_logik.py)

**Testabdeckung:**
- Zufällige Positionsupdate
- Schwellwert-Entfernung
- Mehrere Objekte gleichzeitig
- Error-Handling (ValueError)
- Höchster X-Wert wird zurückgegeben

---

## 2. Main Module

### Übersicht
Das Main Module koordiniert die Kommunikation zwischen Vision, Motion und den ROS2-Nodes.

### Komponenten

#### `PositionPredictionNode` (`postion_prediction_node.py`)
ROS2-Node für die Verarbeitung von Bilddaten und Publikation von Vorhersagen.

**Subscriptions:**
- `/NimSortImageData` - Bilddaten von der Kamera

**Publications:**
- `/NimSortPrediction` - Vorhersagte Objekt-Positionen

**Timer:**
- `main_order` - Periodische Verarbeitung (0.1s Intervall)

### Nachrichtentypen

#### `NimSortImageData`
Input-Nachricht mit Bilddaten

#### `NimSortPrediction`
Output-Nachricht mit Vorhersagen

### Workflow

```
ImageData (Input)
    |
    v
image_data_callback
    |
    v
PositionPredictionLogic.set_object_data()
    |
    v
main_order Timer
    |
    v
PositionPredictionLogic.calculate_next_object_position()
    |
    v
NimSortPrediction (Output)
```

---

## 3. Motion Module

### Übersicht
Das Motion Module ist verantwortlich für die physische Bewegungssteuerung des Roboters.

### Komponenten

#### Roboterarme Steuerung
Kommunikation mit den mechanischen Systemen zur Umsetzung der Sortierungsbefehle.

**Verbindung zu Main:**
- Empfängt Positionsvorhersagen von `NimSortPrediction`
- Steuert Roboterbewegungen basierend auf Zielposition
- Sendet Feedback über Bewegungsstatus

### Schnittstellen

| Interface | Richtung | Beschreibung |
|-----------|----------|-------------|
| Vorhersage-Input | Input | Position des naechsten Objekts |
| Bewegungs-Commands | Output | Befehle an Roboterarme |
| Status-Feedback | Output | Aktueller Bewegungsstatus |

### Integration

Das Motion Module nutzt die Positionsvorhersagen des Main Modules, um:
1. Den Roboter zur richtigen Zeit zu positionieren
2. Das Objekt zu erfassen
3. Es zum Zielort zu bringen

---

## Zusammenhang der Module

```
┌─────────────────────────────────────────┐
│         Vision Module                   │
│  (Objekterkennung + Vorhersage)        │
│  PositionPredictionLogic                │
└──────────────┬──────────────────────────┘
               │ NimSortPrediction
               v
┌─────────────────────────────────────────┐
│         Main Module                     │
│  (ROS2 Node + Koordination)             │
│  PositionPredictionNode                 │
└──────────────┬──────────────────────────┘
               │ Bewegungsbefehle
               v
┌─────────────────────────────────────────┐
│         Motion Module                   │
│  (Robotersteuerung)                     │
│  Roboterarme + Aktuatoren               │
└─────────────────────────────────────────┘
```

---

## Weitere Ressourcen

- Architektur-Entscheidungen (architecture-decision.md)
- Logging-Richtlinien (logging.md)
- Projektplanung (projektplanung.md)
