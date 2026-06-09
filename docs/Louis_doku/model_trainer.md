# `model_trainer.py` -- Klassifikatortraining für NimSort

## Zweck

Dieses Skript trainiert den Objektklassifikator. Es liest extrahierte Hu-Moment-Features aus einer CSV-Datei, bewertet ein `DecisionTreeClassifier`-Modell per stratifizierter Kreuzvalidierung und speichert das finale Modell als `.joblib`-Datei, bereit zum Laden durch `feature_detection.py`.

Das Skript ist kein importierbares Modul, sondern wird einmalig manuell ausgeführt, wenn Trainingsdaten vorliegen oder das Modell neu trainiert werden soll.

---

## Abhängigkeiten

```python
import os, joblib, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_val_score
from sklearn.tree import DecisionTreeClassifier, plot_tree
```

| Import | Zweck |
|--------|-------|
| `pandas` | CSV-Laden und Feature-Extraktion |
| `sklearn` | Modell, Kreuzvalidierung, Metriken |
| `matplotlib` | Konfusionsmatrix- und Baumplot |
| `joblib` | Modell serialisieren |

`matplotlib.use("Agg")` erzwingt das dateibasierte Backend, das Skript kann damit auch ohne Display (z.B. auf einem Server) ausgeführt werden.

---

## Pfade & Konfiguration

```python
CSV_PATH = os.path.join(os.path.dirname(__file__), "features.csv")
OUT_PATH = os.path.join(os.path.dirname(__file__), "object_classifier.joblib")
CLASSES  = ["einhorn", "katze", "kreis", "quadrat"]
FEATURES = ["hu_0", "hu_3"]
```

| Variable | Bedeutung |
|----------|-----------|
| `CSV_PATH` | Eingabedaten: extrahierte Features pro Objekt |
| `OUT_PATH` | Ausgabe: serialisiertes Modell für `feature_detection.py` |
| `CLASSES` | Geordnete Klassenliste, Index entspricht der Klassen-ID |
| `FEATURES` | Verwendete Spalten aus der CSV (Hu-Momente) |

> Die Reihenfolge von `CLASSES` ist bedeutsam: `CLASSES.index("katze") == 1` ergibt die Klassen-ID, die `feature_detection.py` zurückgibt.

---

## Ablauf

### 1. Daten laden

```python
df = pd.read_csv(CSV_PATH)
X  = df[FEATURES].values.astype(np.float32)
y  = np.array([CLASSES.index(l) for l in df["label"]], dtype=np.int64)
```

Die CSV enthält mindestens die Spalten `hu_0`, `hu_3` und `label`. Labels werden in Integer-Indizes übersetzt, da `DecisionTreeClassifier` numerische Targets erwartet.

**Erwartetes CSV-Format:**

```
hu_0,hu_3,label
1.2345,3.4567,katze
0.9876,2.1234,kreis
...
```

---

### 2. Modell & Kreuzvalidierung

```python
model  = DecisionTreeClassifier(max_depth=5, random_state=1)
cv     = StratifiedKFold(n_splits=10, shuffle=True, random_state=1)
scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy")
y_pred = cross_val_predict(model, X, y, cv=cv)
```

**Stratifizierte 10-Fold-Kreuzvalidierung** stellt sicher, dass jede Klasse in jedem Fold proportional vertreten ist — wichtig bei ungleicher Klassenhäufigkeit. `random_state=1` macht Ergebnisse reproduzierbar.

`cross_val_score` liefert die Accuracy pro Fold; `cross_val_predict` sammelt Out-of-Fold-Predictions für die Konfusionsmatrix.

**Ausgabe:**

```
[TRAIN] Accuracy: 0.9750 ± 0.0200
              precision  recall  f1-score   support
     einhorn       ...
      katze        ...
      ...
```

**Modellparameter:**

| Parameter | Wert | Begründung |
|-----------|------|------------|
| `max_depth` | 5 | Begrenzt Overfitting bei nur zwei Features |
| `random_state` | 1 | Reproduzierbarkeit |

---

### 3. Finales Training & Visualisierung

```python
model.fit(X, y)   # Modell auf ALLEN Daten trainieren
```

Nach der Kreuzvalidierung wird das Modell auf dem vollständigen Datensatz trainiert — das ist das Modell, das gespeichert und in der Produktion verwendet wird.

Anschließend werden zwei Plots in einer Figur erstellt und als `confusion_matrix.png` gespeichert:

**Linke Achse — Konfusionsmatrix:**
```python
ConfusionMatrixDisplay(confusion_matrix(y, y_pred), display_labels=CLASSES).plot(...)
```
Basiert auf den Out-of-Fold-Predictions (nicht auf dem finalen Modell) — zeigt damit eine realistische Schätzung der Generalisierungsfähigkeit.

**Rechte Achse — Entscheidungsbaum:**
```python
plot_tree(model, feature_names=FEATURES, class_names=CLASSES, filled=True, ...)
```
Visualisiert die gelernten Entscheidungsgrenzen im `hu_0`/`hu_3`-Raum. Nützlich zur Nachvollziehbarkeit, welche Feature-Werte welche Klasse auslösen.

---

### 4. Modell speichern

```python
joblib.dump(model, OUT_PATH)
```

Serialisiert das finale Modell als `object_classifier.joblib`. Diese Datei wird von `feature_detection.py` beim Start geladen.

---

## Ausführung

```bash
python model_trainer.py
```

Das Skript erzeugt zwei Dateien im eigenen Verzeichnis:

| Datei | Inhalt |
|-------|--------|
| `object_classifier.joblib` | Trainiertes Modell (für Produktion) |
| `confusion_matrix.png` | Konfusionsmatrix + Baum-Visualisierung (für Analyse) |

---

## Datenfluss

```
features.csv
    └─► X [hu_0, hu_3], y [Klassen-IDs]
        └─► StratifiedKFold (10 Splits)
            ├─► cross_val_score  → Accuracy pro Fold → mean ± std
            └─► cross_val_predict → y_pred (Out-of-Fold)
                └─► classification_report + confusion_matrix → confusion_matrix.png
        └─► model.fit(X, y)  (alle Daten)
            └─► joblib.dump → object_classifier.joblib
```

---

## Einordnung im NimSort-System

Dieses Skript steht am Anfang der ML-Kette: Es verbraucht die von einem separaten Feature-Extraktionsskript erzeugte `features.csv` und produziert `object_classifier.joblib`, das von `feature_detection.py` zur Laufzeit geladen wird. Es muss nur erneut ausgeführt werden, wenn neue Trainingsdaten vorliegen oder das Modell angepasst werden soll.