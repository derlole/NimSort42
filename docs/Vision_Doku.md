# NimSort Vision – Code Dokumentation

## Übersicht

Das NimSort-Vision-Modul ist eine ROS 2-basierte Bildverarbeitungspipeline zur Erkennung und Klassifizierung von Objekten auf einem Förderband. Es besteht aus drei Hauptkomponenten:

| Modul | Datei | Aufgabe |
|---|---|---|
| `OpencvPipeline` | `opencv_pipeline.py` | Bildaufnahme, ROI-Verarbeitung, Koordinatentransformation |
| `FeatureDetection` | `feature_detection.py` | ML-basierte Objektklassifizierung |
| `Vision` (Node) | `camera_supreme_commander.py` | ROS 2 Node, orchestriert die gesamte Pipeline |

---

## Architektur

```
Kamera
  │
  ▼
OpencvPipeline
  ├── captureImage()       → Rohbild aufnehmen
  └── getImageData()       → ROI maskieren, Konturen finden, Weltkoordinaten berechnen
                                        │
                                        ▼
                           FeatureDetection
                               └── getFeature()   → Objekt-Typ klassifizieren
                                        │
                                        ▼
                               ConveyorSpeedEstimator
                               └── update()        → Förderband-Geschwindigkeit schätzen
                                        │
                                        ▼
                               Vision (ROS 2 Node)
                               ├── /NimSortImageData        (Publisher)
                               └── /NimSortConveyorbeltSpeed (Publisher)
```

---

## Modul: `OpencvPipeline`

**Datei:** `opencv_pipeline.py`  
**Basisklasse:** `OpencvPipelineInterface`

Verwaltet die Kameraverbindung, verarbeitet Rohbilder und berechnet Weltkoordinaten für erkannte Objekte.

### Konstruktor `__init__(camera_index)`

| Parameter | Typ | Beschreibung |
|---|---|---|
| `camera_index` | `int` | Index der Kamera (Standard: `CAMERA_INDEX` aus Config) |

**Initialisierungsschritte:**
- Öffnet Kameraverbindung via `cv.VideoCapture`
- Berechnet die **Homographiematrix** `H` aus Kalibrierungspunkten (`PIXEL_PUNKTE`, `WELT_PUNKTE`)
- Berechnet die **Bounding Box** des Trapez-ROI einmalig für effiziente Array-Slices
- Erstellt die **Trapez-Maske** (relative Koordinaten zur Bounding Box)
- Legt Ausgabeverzeichnisse an (`images_live/raw`, `images_live/roi`, `images_live/bin`)

---

### Methode `captureImage()`

Liest exklusiv einen Rohframe von der Kamera.

- Speichert den Frame in `self._raw_image`
- Setzt `self.time_stamp_ms` (Unix-Timestamp in Millisekunden)
- Wirft `Exception` bei fehlgeschlagener Aufnahme

---

### Methode `getImageData()`

Verarbeitet das zuletzt aufgenommene Bild und gibt erkannte Objekte zurück.

**Rückgabe:** `(objects, time_stamp_ms, thresh)`

| Rückgabewert | Typ | Beschreibung |
|---|---|---|
| `objects` | `List[Tuple[float, float, float]]` | Liste von `(X_m, Y_m, Z_m)` in Weltkoordinaten |
| `time_stamp_ms` | `int` | Aufnahmezeitpunkt in ms |
| `thresh` | `np.ndarray` | Binärbild (für nachgelagerte Klassifizierung) |

**Verarbeitungsschritte:**

1. **ROI-Ausschnitt** – Bild auf Bounding Box des Trapezes zuschneiden
2. **Maskierung** – Trapez-Maske anwenden (`cv.bitwise_and`)
3. **Graustufen & Blur** – Konvertierung + Gaußscher Weichzeichner (5×5)
4. **Otsu-Schwellwert** – Automatische Binarisierung; wird auf Null gesetzt, wenn `otsu_val < MIN_OTSU_THRESHOLD`
5. **Konturerkennung** – `cv.findContours`, gefiltert nach `MIN_CONTOUR_AREA`
6. **Sortierung** – Konturen nach X-Schwerpunkt absteigend sortiert
7. **Pickpunkt-Berechnung** – Schwerpunkt wird um `PICK_OFFSET_PX` in Richtung des nächsten Konturpunkts verschoben
8. **Koordinatentransformation** – Pixel → Weltkoordinaten via Homographie, dann mm → m
9. **Y-Achse negieren** – Anpassung an Roboterkoordinatensystem
10. **Plausibilitätsprüfung** – Koordinaten über `PlausibilityCheck.check_position()` validieren

---

### Methode `pixelToWorld(u, v)`

Transformiert einen Bildpunkt in Weltkoordinaten (mm) mittels der Homographiematrix.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `u` | `float` | Pixelkoordinate X |
| `v` | `float` | Pixelkoordinate Y |

**Rückgabe:** `(X_world_mm, Y_world_mm)`

---

### Methode `convert_mm_to_m(x_mm, y_mm, z_mm)`

Konvertiert Koordinaten von Millimeter in Meter.

**Rückgabe:** `(x_m, y_m, z_m)`

---

### Methode `release()`

Gibt die Kameraressource frei (`self._cap.release()`).

---

## Modul: `FeatureDetection`

**Datei:** `feature_detection.py`  
**Basisklasse:** `FeatureDetectionInterface`

Klassifiziert alle Objekte im Binärbild mithilfe eines trainierten Machine-Learning-Modells (Hu-Momente als Features).

### Konstruktor `__init__(model_path)`

| Parameter | Typ | Beschreibung |
|---|---|---|
| `model_path` | `str` | Pfad zur `.joblib`-Modelldatei (Standard: `object_classifier.joblib` im selben Verzeichnis) |

Lädt das Modell via `joblib.load()`. Wirft `FileNotFoundError`, wenn die Datei nicht gefunden wird.

---

### Statische Methode `_extract_features_for_contours(binary_image)`

Interne Hilfsmethode – extrahiert Feature-Vektoren für alle gültigen Konturen.

**Feature-Extraktion:**
- Berechnet **Hu-Momente** für jede Kontur
- Wendet logarithmische Transformation an: `hu_log = -sign(hu) * log10(|hu| + 1e-10)`
- Verwendet `hu_0` und `hu_3` als zweidimensionalen Feature-Vektor

**Rückgabe:** `List[(feature_vector, contour)]`

---

### Methode `getFeature(binary_image)`

Klassifiziert alle Objekte im übergebenen Binärbild.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `binary_image` | `np.ndarray` | Binärbild (Pixelwerte 0 oder 255) |

**Rückgabe:** `List[int]` – Liste von Klassen-IDs (z.B. `[0, 2, 3]`)

Die Klassen-IDs werden über `LABEL_MAP` aus der Config in lesbare Namen aufgelöst.

---

### Methode `getLastFeature()`

Gibt die zuletzt berechnete Feature-Liste zurück.

---

### Methode `resetFeatureDetection()`

Setzt `_last_feature` auf eine leere Liste zurück.

---

## Modul: `Vision` (ROS 2 Node)

**Datei:** `camera_supreme_commander.py`  
**Node-Name:** `camera_supreme_commander`

Orchestriert die gesamte Vision-Pipeline als ROS 2 Node. Verwaltet Kamera, Feature-Erkennung und Geschwindigkeitsschätzung und publiziert die Ergebnisse.

### Parameter

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `camera_index` | `int` | `4` | Kamera-Index für `OpencvPipeline` |

### Publisher

| Topic | Nachrichtentyp | Beschreibung |
|---|---|---|
| `/NimSortImageData` | `NimSortImageData` | Objektposition (WCS) + Objekttyp + Zeitstempel |
| `/NimSortConveyorbeltSpeed` | `NimSortConveyorbeltSpeed` | Geschätzte Förderband-Geschwindigkeit |

### Timer

| Intervall | Callback |
|---|---|
| 100 ms | `main_order()` |

---

### Methode `main_order()`

Haupt-Callback, der alle 100 ms ausgeführt wird.

**Ablauf:**

```
1. pipeline.captureImage()
2. pipeline.getImageData()       → objects, ts, image
3. speed_calc.update()           → Förderband-Geschwindigkeit schätzen
4. feature_detector.getFeature() → Objekttypen klassifizieren
5. Konsistenzprüfung: len(objects) == len(features)?
6. Ergebnisse publizieren
```

**Fehlerbehandlung:**

| Fehlerfall | Verhalten |
|---|---|
| `RuntimeError` bei Bildaufnahme | Fehler geloggt, kein Publish |
| `ValueError` (keine Konturen / unplausibler Wert) | Dummy-Daten publiziert: `(-1.0, -1.0, -1.0, -1, -1)` |
| `len(objects) != len(features)` | Fehler geloggt, Dummy-Daten publiziert, `return` |
| Keine Geschwindigkeit verfügbar | Fallback: `speed = 0.01` m/s |

---

### Methode `publish_image_data(x_wcs, y_wcs, z_wcs, ts, object_type)`

Erstellt und publiziert eine `NimSortImageData`-Nachricht.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `x_wcs` | `float` | X-Position in Weltkoordinaten (m) |
| `y_wcs` | `float` | Y-Position in Weltkoordinaten (m) |
| `z_wcs` | `float` | Z-Position in Weltkoordinaten (m) |
| `ts` | `int` | Zeitstempel in ms |
| `object_type` | `int` | Klassifizierter Objekttyp |

---

### Methode `publish_conveyorbelt_speed(conveyorbelt_speed)`

Erstellt und publiziert eine `NimSortConveyorbeltSpeed`-Nachricht.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `conveyorbelt_speed` | `float` | Förderband-Geschwindigkeit in m/s |

---

## Konfigurationsparameter

Die folgenden Konstanten werden aus `configs/config_camera` importiert:

| Konstante | Beschreibung |
|---|---|
| `CAMERA_INDEX` | Standard-Kameraindex |
| `MIN_CONTOUR_AREA` | Mindestkonturfläche in Pixel² |
| `Z_W_CONSTANT_IN_MM` | Konstante Z-Höhe des Förderbands in mm |
| `MIN_OTSU_THRESHOLD` | Untergrenze für Otsu-Schwellwert |
| `ROI_TRAPEZ` | Trapez-Eckpunkte für den ROI (Pixel) |
| `PIXEL_PUNKTE` | Kalibrierungspunkte im Bild (für Homographie) |
| `WELT_PUNKTE` | Entsprechende Weltkoordinaten (für Homographie) |
| `PICK_OFFSET_PX` | Offset des Pickpunkts vom Schwerpunkt in Pixel |
| `LABEL_MAP` | Mapping von Klassen-ID zu Objektbezeichnung |

---

## Abhängigkeiten

| Paket | Verwendung |
|---|---|
| `opencv-python` (`cv2`) | Bildverarbeitung, Konturerkennung, Homographie |
| `numpy` | Array-Operationen, Vektorrechnung |
| `joblib` | Laden des ML-Klassifikators |
| `rclpy` | ROS 2 Python-Client |
| `tf2_ros` | Koordinatentransformationen (importiert, derzeit nicht aktiv genutzt) |
| `nimsort_msgs` | Eigene ROS 2-Nachrichtentypen |

---

## Hinweise zur Weiterentwicklung

- Die auskommentierten `cv.imwrite`-Aufrufe in `opencv_pipeline.py` dienen zum Debug-Logging und können zur Fehlersuche temporär aktiviert werden.
- Der `ConveyorSpeedEstimator` schätzt die Geschwindigkeit anhand der X-Position des ersten erkannten Objekts – bei mehreren Objekten wird nur `objects[0]` herangezogen.
- Das ML-Modell (`object_classifier.joblib`) muss vor dem ersten Start mit `train_classifier.py` erzeugt werden.
- Bei `speed = None` wird ein Fallback von `0.01 m/s` publiziert, um nachgelagerte Komponenten nicht zu blockieren.  