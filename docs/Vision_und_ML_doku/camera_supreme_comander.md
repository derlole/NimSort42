# `camera_supreme_commander.py` -- ROS 2 Vision Node für NimSort

## Zweck

Diese ROS2-Node ist der zentrale Orchestrator der NimSort-Visioon. Er koordiniert die Kamera-Pipeline, die Geschwindigkeitsschätzung des Förderbands und die Objektklassifikation, publiziert die Ergebnisse als ROS-Topics an nachgelagerte Systeme.

Die Node trägt den Namen `camera_supreme_commander` und läuft als `Vision`-Klasse, die von `rclpy.node.Node` erbt.

---

## Abhängigkeiten

| Name | Version |
|------|---------|
| rclpy | 2.0+ |
| geometry_msgs | 2.0+ |
| nimsort_msgs | Custom |
| nimsort_vision | Custom |
| nimsort_feature_detection | Custom |

---

## Topics

### Publiziert

| Topic | Message-Typ | Inhalt |
|-------|-------------|--------|
| `/NimSortImageData` | `NimSortImageData` | Position (x, y, z in m), Objekttyp (int), Zeitstempel (ms) |
| `/NimSortConveyorbeltSpeed` | `NimSortConveyorbeltSpeed` | Aktuelle Bandgeschwindigkeit in m/s |

---

## Parameter

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `camera_index` | `int` | `4` | OpenCV-Kameraindex, überschreibbar per Launch-File |

```bash
# Beispiel: anderen Kameraindex setzen
ros2 run nimsort_vision camera_supreme_commander --ros-args -p camera_index:=0
```

---

## Klasse `Vision()`

Initialisiert alle Subsysteme in dieser Reihenfolge:

1. ROS 2-Node `camera_supreme_commander` registrieren
2. Parameter `camera_index` deklarieren und lesen
3. Publisher für `/NimSortImageData` und `/NimSortConveyorbeltSpeed` erstellen
4. Timer mit 0.1 s Intervall (10 Hz) → Callback `main_order`
5. `OpencvPipeline`, `ConveyorSpeedEstimator` und `FeatureDetection` instanziieren

Jedes Subsystem wird einzeln in einem `try/except`-Block initialisiert. Bei `RuntimeError` wird der Fehler geloggt und die Exception weitergegeben, die Node startet dann nicht.

---

### `main_order()` *(Timer-Callback, 10 Hz)*

Kernschleife des Nodes. Wird alle 100 ms vom ROS-Timer aufgerufen.

#### Schritt 1: Bildaufnahme & Objekterkennung

```python
self.pipeline.captureImage()
objects, ts, image = self.pipeline.getImageData()
```

- `objects`: Liste von `(X_m, Y_m, Z_m)` --> Pickpoint aller erkannten Objekte in Weltkoordinaten
- `ts`: Unix-Zeitstempel in ms des aufgenommenen Frames
- `image`: Binärbild für die nachgelagerte Klassifikation

Bei `ValueError` (keine Konturen / unplausible Koordinaten) wird ein Dummy-Datensatz `(-1, -1, -1, -1, -1)` publiziert, um nachgelagerte Nodes über das Ausbleiben eines Objekts zu informieren.

#### Schritt 2: Bandgeschwindigkeit schätzen

```python
speed = self.speed_calc.update(objects[0][0], ts)
```

Die X-Position des ersten (rechtesten) Objekts wird an den `ConveyorSpeedEstimator` übergeben. Gibt `update()` `None` oder `<= 0` zurück (z.B. erstes Frame oder Schätzfehler), wird der zuletzt bekannte Wert `last_speed` verwendet. Ist auch dieser nicht verfügbar, wird als Fallback `0.01 m/s` publiziert.

#### Schritt 3: Objektklassifikation

```python
features = self.feature_detector.getFeature(image)
```

Gibt eine Liste von Klassen-IDs zurück, eine pro erkannter Kontur im Binärbild.

| ID | Objeckt |
|-------|--------|
| `0` | Einhorn |
| `1` | Katze |
| `2` | Kreis |
| `3` | Quadrat |


#### Schritt 4: Konsistenzprüfung & Publizieren

```python
if len(objects) != len(features):
    self.publish_image_data(-1.0, -1.0, -1.0, -1, -1)
    return
```

Stimmt die Anzahl erkannter Objekte nicht mit der Anzahl klassifizierter Features überein, wird ein Fehler geloggt und ein Dummy publiziert. Dieser Fall kann auftreten, wenn Pipeline und Feature-Detektor die Konturanzahl unterschiedlich bestimmen.

Bei Übereinstimmung werden alle Objekte einzeln publiziert:

```python
for i in range(len(objects)):
    x_w, y_w, z_w = objects[i]
    self.publish_image_data(x_w, y_w, z_w, ts, features[i])
```

---

### `publish_image_data(x, y, z, ts, object_type)`

Befüllt eine `NimSortImageData`-Message und publiziert sie auf `/NimSortImageData`.

| Feld | Typ | Inhalt |
|------|-----|--------|
| `current_pickpoin_wcs` | `Point` | X, Y, Z in Metern (Weltkoordinaten) |
| `object_type` | `int` | Klassen-ID aus `FeatureDetection` |
| `ts` | `int` | Unix-Zeitstempel in ms |

Dummy-Werte `(-1.0, -1.0, -1.0, -1, -1)` signalisieren: kein Objekt erkannt oder Fehler aufgetreten.

---

### `publish_conveyorbelt_speed(speed)`

Befüllt eine `NimSortConveyorbeltSpeed`-Message und publiziert sie auf `/NimSortConveyorbeltSpeed`.

---

## Fehlerbehandlung

| Fehlerart | Reaktion |
|-----------|----------|
| `RuntimeError` bei Bildaufnahme | Fehler geloggt, kein Publish |
| `ValueError` (keine Objekte) | Dummy `(-1,-1,-1,-1,-1)` publiziert |
| `RuntimeError` bei Geschwindigkeit | Fehler geloggt, Fallback auf `last_speed` |
| `RuntimeError` bei Klassifikation | Fehler geloggt |
| Anzahl-Mismatch Objekte/Features | Fehler geloggt, Dummy publiziert, Return |

---

## `main()`

```python
rclpy.init(args=args)
node = Vision()
executor = MultiThreadedExecutor()
executor.add_node(node)
executor.spin()
```

Der `MultiThreadedExecutor` ermöglicht parallele Callback-Ausführung. Bei `ExternalShutdownException` (z.B. `ros2 lifecycle` oder `Ctrl+C`) und unerwarteten Exceptions wird sauber heruntergefahren:

```python
finally:
    executor.shutdown()
    rclpy.shutdown()
```

---

## Datenfluss

```
Timer (10 Hz) → main_order()
    │
    ├─► OpencvPipeline.captureImage()
    │       └─► OpencvPipeline.getImageData()
    │               └─► objects [(x,y,z), ...], ts, binary_image
    │
    ├─► ConveyorSpeedEstimator.update(objects[0].x, ts)
    │       └─► speed [m/s]  → /NimSortConveyorbeltSpeed
    │
    ├─► FeatureDetection.getFeature(binary_image)
    │       └─► features [int, ...]
    │
    └─► Konsistenzprüfung len(objects) == len(features)
            └─► für jedes Objekt: publish_image_data()
                    └─► /NimSortImageData
```

---

## Einordnung im NimSort-System

`camera_supreme_commander.py` ist die einzige ROS 2-Node im Vision-Stack und bildet die Schnittstelle zwischen der Kamera-Hardware und dem Rest des ROS-Graphen. Alle anderen Module (`opencv_pipeline.py`, `feature_detection.py`, `conveyor_speed.py`) sind reine Python-Klassen ohne ROS-Abhängigkeit.