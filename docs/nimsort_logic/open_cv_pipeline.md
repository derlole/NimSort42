# `opencv_pipeline.py` -- Bildverarbeitungs-Pipeline für NimSort

## Zweck

Dieses Modul implementiert die zentrale OpenCV-Bildverarbeitungs-Pipeline. Es kapselt den gesamten Weg vom Rohframe der Förderbandkamera bis zur Ausgabe von den Aktuellen Position der Objekte in  Weltkoordinaten.

Die Klasse `OpencvPipeline` implementiert das Interface `OpencvPipelineInterface` und arbeitet eng mit `PlausibilityCheck` sowie den Kamera-Konfigurationsparametern aus `config_camera` zusammen.

---

## Abhängigkeiten

| Name | Version |
|------|---------|
| opencv-python | 4.13.0 |
| numpy | 1.26.0+ |
| nimsort_vision | Custom |
| configs | Custom |

---

## Klasse `OpencvPipeline`

### `__init__(camera_index=CAMERA_INDEX)`

Initialisiert die Pipeline und bereitet alle rechenintensiven Strukturen einmalig vor.

**Schritte:**

1. Verzeichnisse für Debug-Bilder anlegen (`images_live/raw`, `roi`, `bin`)
2. Kamera öffnen via `cv.VideoCapture`, wirft `RuntimeError` bei Fehler
3. **Homographie-Matrix `H`** berechnen aus `PIXEL_PUNKTE` → `WELT_PUNKTE` (`cv.findHomography`)
4. **Bounding Box des ROI-Trapezes** einmalig vorberechnen (`cv.boundingRect`) → schneller Array-Slice
5. **Trapez-Maske** relativ zur Bounding Box vorberechnen (`cv.fillPoly`) → wird in jeder `getImageData()`-Aufruf wiederverwendet

> Die Vorberechnung von Maske und Slice in `__init__` ist eine bewusste Performance-Optimierung, da diese Strukturen frame-konstant sind.

---

### `captureImage()`

```python
def captureImage(self)
```

Liest exklusiv den nächsten Rohframe von der Kamera ein und speichert den Zeitstempel.

- Setzt `self._raw_image` und `self.time_stamp_ms` (Unix-Zeit in ms).
- Inkrementiert internen `_test_counter` (für Debug-Dateinamen).
- Wirft `Exception` wenn `cap.read()` fehlschlägt.

---

### `getImageData()`

```python
def getImageData(self) -> tuple[list, int, np.ndarray]
```

Verarbeitet das zuletzt aufgenommene Bild vollständig und gibt die Position der erkannten Objekte in Weltkoordinaten zurück.

**Rückgabe:** `(objects, time_stamp_ms, thresh)`

| Feld | Typ | Inhalt |
|------|-----|--------|
| `objects` | `list[tuple]` | Liste von `(X_m, Y_m, Z_m)` pro erkanntem Objekt |
| `time_stamp_ms` | `int` | Zeitstempel des zugehörigen Frames |
| `thresh` | `np.ndarray` | Binärbild nach Otsu-Schwellwert (für Machine Learning) |



#### Verarbeitungsschritte im Detail:

**1. ROI-Ausschnitt & Trapezmaske**
- Array-Slice schneidet Bounding Box des Trapezes aus dem Rohbild
- `bitwise_and` mit Trapezmaske maskiert Pixel außerhalb des ROI

**2. Graustufen & Weichzeichnung**
- BGR → Graustufen-Konvertierung
- Gauß-Blur (5×5) reduziert Rauschen vor Schwellwertbildung

**3. Otsu-Schwellwert**
- Otsu bestimmt optimalen Schwellwert automatisch aus Grauwertverteilung
- Liegt `otsu_val` unter `MIN_OTSU_THRESHOLD` → Binärbild wird leer gesetzt (verhindert Falschdetektionen bei leerem Band)

**4. Konturerkennung & Filterung**
- `RETR_EXTERNAL`: nur äußere Konturen
- `CHAIN_APPROX_NONE`: alle Konturpunkte (nötig für spätere Berechnungen)
- Konturen unter `MIN_CONTOUR_AREA` werden verworfen (Rauschartefakte)
- Sortierung nach X-Schwerpunkt (rechts → links, absteigend)

**5. Schwerpunkt & Pickpunkt**
- Schwerpunkt aus Bildmomenten (`m10/m00`, `m01/m00`)
- ROI-lokale Koordinaten → Vollbild-Koordinaten durch Addition von `_rx`, `_ry`
- Pickpunkt wird vom nächsten Konturpunkt weg Richtung Schwerpunkt verschoben (`PICK_OFFSET_PX`), damit Greifpunkt weiter im Objektinneren liegt

**6. Homographie: Pixel → Welt** 
- `pixelToWorld` wandelt die Pikelkoordinaten in Weltkoordinaten.
- Z aus Konfigurationskonstante `Z_W_CONSTANT_IN_MM` (Förderbandebene fix)
- mm → m Konvertierung, Y-Achse invertiert (Pixel-Y ↓, Welt-Y ↑)

**7. Plausibilitätsprüfung**
- Koordinaten außerhalb des definierten Arbeitsraums werden mit `ValueError` verworfen

---

### `getLastImageData()`

```python
def getLastImageData(self) -> tuple | None
```

Gibt das Ergebnis des letzten `getImageData()`-Aufrufs zurück, ohne erneute Verarbeitung.

---

### `release()`

```python
def release(self)
```

Gibt die Kameraressource frei. Sollte beim Beenden des Nodes aufgerufen werden.

---

## Datenfluss

```
captureImage()
    └─► cap.read() → _raw_image + time_stamp_ms

getImageData()
    └─► ROI-Slice + Trapezmaske
        └─► Graustufen → GaussianBlur → Otsu-Threshold
            └─► findContours → Filterung → Sortierung
                └─► Schwerpunkt → Pickpunkt-Offset
                    └─► pixelToWorld (Homographie)
                        └─► mm → m + Y-Invertierung
                            └─► PlausibilityCheck
                                └─► return (objects, timestamp, thresh)
```

---

## Konfigurationsparameter (aus `config_camera`)

| Parameter | Bedeutung |
|-----------|-----------|
| `CAMERA_INDEX` | Index der Kamera (`cv.VideoCapture`) |
| `ROI_TRAPEZ` | Eckpunkte des Förderband-ROI als Polygon |
| `PIXEL_PUNKTE` | Pixelkoordinaten der Homographie-Referenzpunkte |
| `WELT_PUNKTE` | Zugehörige Weltkoordinaten in mm |
| `MIN_CONTOUR_AREA` | Mindestfläche einer gültigen Kontur in px² |
| `MIN_OTSU_THRESHOLD` | Untergrenze für Otsu-Wert (Leerband-Erkennung) |
| `Z_W_CONSTANT_IN_MM` | Konstante Z-Höhe des Förderbands in mm |
| `PICK_OFFSET_PX` | Verschiebung des Pickpunkts in Pixel |

---

## Einordnung im NimSort-System

`OpencvPipeline` ist das Herzstück der Sensorik. Die ROS2-Node `camera_supreme_commander.py` ruft `captureImage()` und `getImageData()` in seiner Timer-Callback-Schleife auf und publiziert die zurückgegebenen Weltkoordinaten als ROS-Topics.

## Rücksprung zur [nimsort_logic](../../documentation/nimsort_logic.md#64-weitere-dokumentation)