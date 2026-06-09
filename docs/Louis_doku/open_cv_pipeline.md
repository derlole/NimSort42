# `opencv_pipeline.py` = Bildverarbeitungs-Pipeline für NimSort

## Zweck

Dieses Modul implementiert die zentrale OpenCV-Bildverarbeitungs-Pipeline des NimSort-Systems. Es kapselt den gesamten Weg vom Rohframe der Förderbandkamera bis zur Ausgabe von Weltkoordinaten erkannter Objekte — bereit zur Weiterverarbeitung durch den ROS 2-Node.

Die Klasse `OpencvPipeline` implementiert das Interface `OpencvPipelineInterface` und arbeitet eng mit `PlausibilityCheck` sowie den Kamera-Konfigurationsparametern aus `config_camera` zusammen.

---

## Abhängigkeiten

```python
import cv2 as cv
import numpy as np
import time, os

from nimsort_vision.opencv_pieline_interface import OpencvPipelineInterface
from nimsort_vision.plausibility_check import PlausibilityCheck
from configs.config_camera import (
    CAMERA_INDEX, MIN_CONTOUR_AREA, Z_W_CONSTANT_IN_MM,
    MIN_OTSU_THRESHOLD, ROI_TRAPEZ, PIXEL_PUNKTE, WELT_PUNKTE, PICK_OFFSET_PX
)
```

| Import | Zweck |
|--------|-------|
| `cv2` | Bildaufnahme, Filterung, Konturerkennung, Homographie |
| `numpy` | Vektoroperationen für Koordinatentransformationen |
| `OpencvPipelineInterface` | Abstrakte Basisklasse (Interface-Vertrag) |
| `PlausibilityCheck` | Validierung berechneter Weltkoordinaten |
| `config_camera` | Kamera-Index, ROI-Trapez, Homographie-Punkte, Schwellwerte |

---

## Klasse `OpencvPipeline`

### `__init__(camera_index=CAMERA_INDEX)`

Initialisiert die Pipeline und bereitet alle rechenintensiven Strukturen einmalig vor.

**Schritte:**

1. Verzeichnisse für Debug-Bilder anlegen (`images_live/raw`, `roi`, `bin`)
2. Kamera öffnen via `cv.VideoCapture` — wirft `RuntimeError` bei Fehler
3. **Homographie-Matrix `H`** berechnen aus `PIXEL_PUNKTE` → `WELT_PUNKTE` (`cv.findHomography`)
4. **Bounding Box des ROI-Trapezes** einmalig vorberechnen (`cv.boundingRect`) → schneller Array-Slice
5. **Trapez-Maske** relativ zur Bounding Box vorberechnen (`cv.fillPoly`) — wird in jeder `getImageData()`-Aufruf wiederverwendet

> Die Vorberechnung von Maske und Slice in `__init__` ist eine bewusste Performance-Optimierung, da diese Strukturen frame-konstant sind.

---

### `captureImage()`

```python
def captureImage(self)
```

Liest exklusiv den nächsten Rohframe von der Kamera und speichert Bild und Zeitstempel intern.

- Setzt `self._raw_image` und `self.time_stamp_ms` (Unix-Zeit in ms)
- Inkrementiert internen `_test_counter` (für Debug-Dateinamen)
- Wirft `Exception` wenn `cap.read()` fehlschlägt

> Bewusst schlank gehalten — enthält keine Bildverarbeitung, damit Latenz und Zeitstempel-Genauigkeit maximiert werden.

---

### `getImageData()`

```python
def getImageData(self) -> tuple[list, int, np.ndarray]
```

Verarbeitet das zuletzt aufgenommene Bild vollständig und gibt erkannte Objekte in Weltkoordinaten zurück.

**Rückgabe:** `(objects, time_stamp_ms, thresh)`

| Feld | Typ | Inhalt |
|------|-----|--------|
| `objects` | `list[tuple]` | Liste von `(X_m, Y_m, Z_m)` pro erkanntem Objekt |
| `time_stamp_ms` | `int` | Zeitstempel des zugehörigen Frames |
| `thresh` | `np.ndarray` | Binärbild nach Otsu-Schwellwert (für Debugging) |

**Verarbeitungsschritte im Detail:**

#### 1. ROI-Ausschnitt & Trapezmaske

```python
roi = self._raw_image[self._roi_slice].copy()
roi_masked = cv.bitwise_and(roi, roi, mask=self._trapez_mask)
```

Der vorberechnete Array-Slice extrahiert die Bounding Box des Trapezes. `bitwise_and` mit der Trapezmaske stellt sicher, dass nur Pixel innerhalb des definierten ROI-Trapezes verarbeitet werden.

#### 2. Graustufen & Weichzeichnung

```python
gray = cv.cvtColor(roi_masked, cv.COLOR_BGR2GRAY)
blur = cv.GaussianBlur(gray, (5, 5), 0)
```

Gaussian Blur (5×5 Kernel) reduziert Bildrauschen vor der Schwellwertbildung.

#### 3. Otsu-Schwellwert

```python
otsu_val, thresh = cv.threshold(blur, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
if otsu_val < MIN_OTSU_THRESHOLD:
    thresh = np.zeros_like(blur)
```

Otsu bestimmt den optimalen Schwellwert automatisch anhand der Grauwertverteilung. Liegt `otsu_val` unter `MIN_OTSU_THRESHOLD` (konfigurierbar), wird das Binärbild leer gesetzt — das verhindert Falschdetektionen bei homogenem, objektfreiem Band.

#### 4. Konturerkennung & Filterung

```python
contours, _ = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
contours = [cnt for cnt in contours if cv.contourArea(cnt) >= MIN_CONTOUR_AREA]
contours = sorted(contours, key=lambda cnt: cv.moments(cnt)["m10"] / cv.moments(cnt)["m00"], reverse=True)
```

- `RETR_EXTERNAL`: nur äußere Konturen
- `CHAIN_APPROX_NONE`: alle Konturpunkte (für spätere Schwerpunkt-/Pickpunkt-Berechnung)
- Filterung nach Mindestfläche (`MIN_CONTOUR_AREA`) entfernt Rauschartefakte
- Sortierung nach X-Schwerpunkt (links → rechts auf dem Band, absteigend)

#### 5. Schwerpunkt & Pickpunkt-Berechnung

```python
M = cv.moments(cnt)
cx_roi = M["m10"] / M["m00"]   # Schwerpunkt im ROI-Koordinatensystem
cy_roi = M["m01"] / M["m00"]

cx_px = cx_roi + self._rx       # Rückrechnung in Vollbild-Pixelkoordinaten
cy_px = cy_roi + self._ry
```

Der Schwerpunkt wird aus den Bildmomenten berechnet und vom ROI-lokalen Koordinatensystem zurück in das Vollbild-Koordinatensystem transformiert.

Anschließend wird der **Pickpunkt** leicht in Richtung Zentroid verschoben — weg vom nächstliegenden Konturpunkt:

```python
# Nächsten Konturpunkt zum Schwerpunkt finden
richtung = S - naechster_punkt
richtung_norm = richtung / np.linalg.norm(richtung)
pick = S + richtung_norm * PICK_OFFSET_PX
```

> Diese Verschiebung stellt sicher, dass der Greifpunkt nicht auf der Objektkante, sondern leicht im Inneren des Objekts liegt.

#### 6. Homographie: Pixel → Weltkoordinaten

```python
X_w, Y_w = self.pixelToWorld(cx_px, cy_px)
X_w_m, Y_w_m, Z_w_m = self.convert_mm_to_m(X_w, Y_w, Z_W_CONSTANT_IN_MM)
Y_w_m = -Y_w_m  # Y-Achse invertieren (Pixel-Y läuft nach unten, Welt-Y nach oben)
```

`pixelToWorld` wendet die Homographie-Matrix `H` an:

```python
def pixelToWorld(self, u, v):
    p = np.array([u, v, 1.0])
    w = self.H @ p
    w /= w[2]           # Homogene Division
    return w[0], w[1]
```

Z wird als Konstante `Z_W_CONSTANT_IN_MM` aus der Konfiguration übernommen (Förderband liegt auf definierter Höhe).

#### 7. Plausibilitätsprüfung

```python
if not self._plausi.check_position([X_w_m, Y_w_m, Z_w_m]):
    raise ValueError(f"Unplausible Koordinaten: ({X_w_m:.2f}, {Y_w_m:.2f}, {Z_w_m:.2f})")
```

Koordinaten außerhalb des erwarteten Arbeitsraums werden verworfen.

---

### `getLastImageData()`

```python
def getLastImageData(self) -> tuple | None
```

Gibt das Ergebnis des letzten `getImageData()`-Aufrufs zurück, ohne erneute Verarbeitung. Nützlich für asynchrone Abfragen aus dem ROS 2-Node.

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

`OpencvPipeline` ist das Herzstück der Sensorik. Der ROS 2-Node `camera_supreme_commander.py` ruft `captureImage()` und `getImageData()` in seiner Timer-Callback-Schleife auf und publiziert die zurückgegebenen Weltkoordinaten als ROS-Topics an den Roboterarm.