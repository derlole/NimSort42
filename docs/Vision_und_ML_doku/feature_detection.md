# `feature_detection.py` -- Objektklassifikation für NimSort

## Zweck

Dieses Modul klassifiziert alle Objekte, die im Binärbild der OpenCV-Pipeline erkannt wurden. Als Features werden zwei logarithmisch transformierte Hu-Momente (`hu_0` und `hu_3`) verwendet, die an ein vortrainiertes Sklearn-Modell übergeben werden. Das Ergebnis ist eine geordnete Liste von Klassen-IDs, eine pro erkanntem Objekt.

Die Klasse `FeatureDetection` implementiert das Interface `FeatureDetectionInterface`.

---

## Abhängigkeiten

| Name | Version |
|------|---------|
| opencv-python | 4.13.0 |
| numpy | 1.26.0+ |
| joblib | 1.3.0+ |
| nimsort_feature_detection | Custom |
| configs | Custom |

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

### `_extract_features_for_contours(binary_image)`

```python
@staticmethod
def _extract_features_for_contours(binary_image: np.ndarray) -> list
```

Extrahiert Features für alle gültigen Konturen im Binärbild.

**Schritte:**

#### 1. Konturerkennung & Filterung


- Findet alle äußeren Konturen im Binärbild.
- Filtert Konturen heraus, deren Fläche kleiner als MIN_CONTOUR_AREA ist.
- Sortiert die verbleibenden Konturen nach ihrer x-Koordinate des Schwerpunkts, absteigend, also von rechts nach links im Bild



Analog zur Logik in `opencv_pipeline.py`.

#### 2. Hu-Momente berechnen & logarithmisch transformieren

- Berechnet die 7 Hu-Momente aus den Bildmomenten (moments).
- Wendet eine Log-Transformation an, um den riesigen Wertebereich der Hu-Momente (bis zu 10⁻³⁰) auf eine für ML-Modelle praktikable Größenordnung zu komprimieren.
- Formel: hu_log[i] = -sign(hu[i]) · log₁₀(|hu[i]| + 1e-10).

- sign(hu[i]) erhält das Vorzeichen der ursprünglichen Werte.
- log₁₀(|hu[i]| + 1e-10) komprimiert den Betrag; das +1e-10 verhindert log10(0) (undefiniert).


- np.errstate(divide="ignore") unterdrückt NumPy-Warnungen, die durch sehr kleine/grenzwertige Werte beim Logarithmus entstehen können.
- Ergebnis (hu_log) sind die transformierten, ML-tauglichen Hu-Momente, die rotations-, translations-, skalierungs- und spiegelungsinvariant sind


#### 3. Feature-Vektor

- Extrahiert aus den log-transformierten Hu-Momenten (hu_log) nur zwei ausgewählte Werte: hu_0 und hu_3.
- Begründung: Diese beiden Momente haben sich in der Trainingsphase als ausreichend trennscharf zur Unterscheidung der Objektklassen erwiesen, die übrigen fünf Hu-Momente werden verworfen.
- Baut daraus einen Feature-Vektor als NumPy-Array der Form (1, 2) mit Datentyp float32.
- Rückgabewert: list[np.ndarray], pro gültiger Kontur ein solcher Feature-Vektor.

---

### `getFeature(binary_image)`

```python
def getFeature(self, binary_image: np.ndarray) -> list[int]
```

Klassifiziert alle Objekte im Binärbild und gibt eine Liste von Klassen-IDs zurück.

**Rückgabe:** z.B. `[0, 2, 3]` eine ID pro erkanntem Objekt, in der Reihenfolge der X-Sortierung.

**Ablauf:**

- Ruft `self._extract_features_for_contours(binary_image) auf, um für jede gültige Kontur im Bild einen Feature-Vektor zu erhalten.
- Iteriert über alle extrahierten Feature-Vektoren (extracted).
- Führt für jeden Feature-Vektor eine Vorhersage mit dem trainierten Modell durch `self._model.predict(feature_vec)`.
- Da predict()` ein sklearn-Array zurückgibt, wird mit [0] der erste (und einzige) Wert extrahiert.
- int() wandelt das Ergebnis (z. B. numpy.int64) in einen normalen Python-Integer um.
- Die Vorhersage (Klassenlabel als Zahl) wird der Liste features hinzugefügt.
- Falls keine Konturen im Bild gefunden wurden, bleibt extracted leer → die Schleife läuft nicht, features bleibt eine leere Liste → Rückgabe ist [].

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

## Konfigurationsparameter (aus `config_camera`)

| Parameter | Bedeutung |
|-----------|-----------|
| `MIN_CONTOUR_AREA` | Mindestfläche einer Kontur in px² (Rauschfilter) |
| `LABEL_MAP` | Dict: Klassen-ID (int) → Bezeichnung (str), z.B. `{0: "Typ_A", 1: "Typ_B"}` |

---

## Einordnung im NimSort-System

`FeatureDetection` wird nach `getImageData()` aufgerufen und empfängt dessen `thresh`-Binärbild direkt. Die zurückgegebene Klassen-ID-Liste wird vom der ROS2-Node `camera_supreme_commander.py` zusammen mit den Weltkoordinaten aus der OpenCV-Pipeline zu einem vollständigen Objektdatensatz zusammengeführt.