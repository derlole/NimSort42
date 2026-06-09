# `feature_detection.py` -- Objektklassifikation für NimSort

## Zweck

Dieses Modul klassifiziert alle Objekte, die im Binärbild der OpenCV-Pipeline erkannt wurden. Als Features werden zwei logarithmisch transformierte Hu-Momente (`hu_0` und `hu_3`) verwendet, die an ein vortrainiertes Sklearn-Modell übergeben werden. Das Ergebnis ist eine geordnete Liste von Klassen-IDs, eine pro erkanntem Objekt.

Die Klasse `FeatureDetection` implementiert das Interface `FeatureDetectionInterface`.

---

## Abhängigkeiten

```python
import cv2 as cv
import numpy as np
import joblib
import os

from nimsort_feature_detection.feature_detection_interface import FeatureDetectionInterface
from configs.config_camera import MIN_CONTOUR_AREA, LABEL_MAP
```

| Import | Zweck |
|--------|-------|
| `cv2` | Konturerkennung, Bildmomente, Hu-Momente |
| `numpy` | Feature-Vektoren, Log-Transformation |
| `joblib` | Laden des trainierten Klassifikators (`.joblib`) |
| `FeatureDetectionInterface` | Abstrakte Basisklasse |
| `MIN_CONTOUR_AREA` | Mindestfläche gültiger Konturen (aus `config_camera`) |
| `LABEL_MAP` | Mapping Klassen-ID → Bezeichnung (aus `config_camera`) |

---

## Modellpfad

```python
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "object_classifier.joblib")
```

Das Modell liegt im selben Verzeichnis wie das Modul und wird beim ersten Import aufgelöst. Es wird mit `model_trainer.py` erzeugt.

---

## Klasse `FeatureDetection`

### `__init__(model_path=_MODEL_PATH)`

Lädt das trainierte Klassifikationsmodell.

- Prüft ob die Datei existiert, wirft `FileNotFoundError` mit Hinweis auf `model_trainer.py` ausführen wenn nicht
- Lädt das Modell via `joblib.load()`
- Initialisiert `_last_feature` als leere Liste

---

### `_extract_features_for_contours(binary_image)` *(statisch)*

```python
@staticmethod
def _extract_features_for_contours(binary_image: np.ndarray) -> list
```

Extrahiert Features für alle gültigen Konturen im Binärbild.

**Schritte:**

#### 1. Konturerkennung & Filterung

```python
contours, _ = cv.findContours(binary_image, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
contours = [cnt for cnt in contours if cv.contourArea(cnt) >= MIN_CONTOUR_AREA]
contours = sorted(contours, key=lambda cnt: cv.moments(cnt)["m10"] / cv.moments(cnt)["m00"], reverse=True)
```

Analog zur Logik in `opencv_pipeline.py`: externe Konturen, Mindestfläche, Sortierung nach X-Schwerpunkt (rechts → links).

#### 2. Hu-Momente berechnen & logarithmisch transformieren

```python
hu_raw = cv.HuMoments(moments).flatten()
with np.errstate(divide="ignore"):
    hu_log = -np.sign(hu_raw) * np.log10(np.abs(hu_raw) + 1e-10)
```

Diese Hu-Momente sind rotations-, translations-, skalierungs- und spiegelungsinvariant, decken aber einen sehr großen Wertebereich ab (bis 10⁻³⁰). Die Transformation `hu_log[i] = -sign(hu[i]) · log₁₀(|hu[i]| + ε)` komprimiert diesen Bereich auf eine für ML-Modelle handhabbare Größenordnung. Der Term `+1e-10` verhindert `log10(0)`, `np.errstate` unterdrückt die entsprechende NumPy-Warnung.

#### 3. Feature-Vektor

```python
hu_0 = hu_log[0]   # Form-Komplexität / Kompaktheit
hu_3 = hu_log[3]   # Asymmetrie höherer Ordnung
feature_vec = np.array([[hu_0, hu_3]], dtype=np.float32)
```

Von den sieben Hu-Momenten werden nur `hu_0` und `hu_3` verwendet, da sich diese beiden in der Trainingsphase als ausreichend trennscharf für die Objektklassen erwiesen haben.

**Rückgabe:** `list[np.ndarray]` ein Feature-Vektor der Form `(1, 2)` pro gültiger Kontur.

---

### `getFeature(binary_image)`

```python
def getFeature(self, binary_image: np.ndarray) -> list[int]
```

Klassifiziert alle Objekte im Binärbild und gibt eine Liste von Klassen-IDs zurück.

**Rückgabe:** z.B. `[0, 2, 3]` eine ID pro erkanntem Objekt, in der Reihenfolge der X-Sortierung.

**Ablauf:**

```python
extracted = self._extract_features_for_contours(binary_image)

for feature_vec in extracted:
    prediction = int(self._model.predict(feature_vec)[0])
    features.append(prediction)
```

Für jeden Feature-Vektor wird `model.predict()` aufgerufen. Die Ausgabe ist ein Sklearn-Array, `[0]` holt den skalaren Wert, `int()` konvertiert ihn.

**Logging:** Pro Objekt wird ausgegeben:
```
[FD]: hu_0=1.2345, hu_3=3.4567 → 2 (Katze)
```

Wenn keine Konturen gefunden werden, wird eine leere Liste zurückgegeben.

---

### `getLastFeature()`

```python
def getLastFeature(self) -> list[int]
```

Gibt das Ergebnis des letzten `getFeature()`-Aufrufs zurück, ohne erneute Berechnung.

---

### `resetFeatureDetection()`

```python
def resetFeatureDetection(self)
```

Setzt `_last_feature` auf eine leere Liste zurück.

---

## Datenfluss

```
binary_image (von getImageData())
    └─► findContours → Filterung nach > MIN_CONTOUR_AREA → X-Sortierung
        └─► cv.moments → cv.HuMoments → log-Transformation
            └─► feature_vec [hu_0, hu_3]
                └─► model.predict(feature_vec)
                    └─► Klassen-ID (int)
                        └─► return [id_0, id_1, ...]
```

---

## Feature-Auswahl: Warum `hu_0` und `hu_3`? #TODO

| Moment | Eigenschaft |
|--------|-------------|
| `hu_0` | Verhältnis von Umfang zu Fläche misst grob die Kompaktheit/Komplexität einer Form |
| `hu_3` | Empfindlich für Asymmetrie und Ausrichtung höherer Ordnung |

Die Kombination dieser beiden Momente reicht aus, um die in NimSort vorkommenden Objektklassen im zweidimensionalen Feature-Raum zu trennen, ohne das Modell zu überparametrisieren.

---

## Konfigurationsparameter (aus `config_camera`)

| Parameter | Bedeutung |
|-----------|-----------|
| `MIN_CONTOUR_AREA` | Mindestfläche einer Kontur in px² (Rauschfilter) |
| `LABEL_MAP` | Dict: Klassen-ID (int) → Bezeichnung (str), z.B. `{0: "Typ_A", 1: "Typ_B"}` |

---

## Einordnung im NimSort-System

`FeatureDetection` wird nach `getImageData()` aufgerufen und empfängt dessen `thresh`-Binärbild direkt. Die zurückgegebene Klassen-ID-Liste wird vom der ROS2-Node `camera_supreme_commander.py` zusammen mit den Weltkoordinaten aus der OpenCV-Pipeline zu einem vollständigen Objektdatensatz zusammengeführt.