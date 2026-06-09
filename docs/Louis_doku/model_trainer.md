# `model_trainer.py` -- Klassifikatortraining für NimSort

## Zweck

Dieses Skript trainiert den Objektklassifikator. Es liest extrahierte Features aus `features.csv`, bewertet ein `DecisionTreeClassifier`-Modell per stratifizierter Kreuzvalidierung und speichert das finale Modell als `.joblib`-Datei, bereit zum Laden durch `feature_detection.py`.

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

`matplotlib.use("Agg")` erzwingt das dateibasierte Backend, das Skript läuft damit auch ohne Display (z.B. auf einem Server).

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
| `CLASSES` | Geordnete Klassenliste; Index = Klassen-ID im Modell |
| `FEATURES` | Zwei der verfügbaren Hu-Momente, die für das Training genutzt werden |

> Die Reihenfolge von `CLASSES` ist bedeutsam: `CLASSES.index("katze") == 1` ergibt die Klassen-ID, die `feature_detection.py` zurückgibt.

---

## CSV-Format (`features.csv`)

Die Datei enthält **677 Samples** mit folgenden Spalten:

| Spalte | Typ | Inhalt |
|--------|-----|--------|
| `label` | string | Klassenname (`einhorn`, `katze`, `kreis`, `quadrat`) |
| `filename` | string | Quelldatei des Samples, z.B. `einhorn_108.jpg` |
| `polygon_vertices` | int | Anzahl der Konturpunkte nach Approximation |
| `hu_0` … `hu_6` | float | Die 7 Hu-Momente des Objekts |
| `fourier_0` … `fourier_9` | float | Erste 10 normalisierte Fourier-Deskriptoren |

Für das Training werden ausschließlich `hu_0` und `hu_3` verwendet (siehe `FEATURES`). Alle weiteren Spalten sind in der CSV vorhanden, werden vom Skript aber nicht genutzt.


---

## Ablauf

### 1. Daten laden

```python
df = pd.read_csv(CSV_PATH)
X  = df[FEATURES].values.astype(np.float32)
y  = np.array([CLASSES.index(l) for l in df["label"]], dtype=np.int64)
print(f"[TRAIN] {len(X)} Samples | Features: {FEATURES}")
```

Aus den 677 Zeilen werden nur `hu_0` und `hu_3` als Feature-Matrix `X` extrahiert. Die Texturlabels werden in Integer-Indizes übersetzt (`einhorn→0`, `katze→1`, `kreis→2`, `quadrat→3`), da `DecisionTreeClassifier` numerische Targets erwartet.

---

### 2. Modell & Kreuzvalidierung

```python
model  = DecisionTreeClassifier(max_depth=5, random_state=1)
cv     = StratifiedKFold(n_splits=10, shuffle=True, random_state=1)
scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy")
y_pred = cross_val_predict(model, X, y, cv=cv)
```

**Stratifizierte 10-Fold-Kreuzvalidierung** stellt sicher, dass jede Klasse in jedem Fold proportional vertreten ist. Relevant, falls die Klassenverteilung leicht ungleich ist. `random_state=1` macht Ergebnisse reproduzierbar.

`cross_val_score` liefert die Accuracy pro Fold; `cross_val_predict` sammelt Out-of-Fold-Predictions für die Konfusionsmatrix.

**Modellparameter:**

| Parameter | Wert | Begründung |
|-----------|------|------------|
| `max_depth` | 5 | Begrenzt Overfitting bei nur zwei Features |
| `random_state` | 1 | Reproduzierbarkeit |

**Konsolenausgabe:**
```
[TRAIN] 677 Samples | Features: ['hu_0', 'hu_3']
[TRAIN] Accuracy: 0.XXXX ± 0.XXXX
              precision  recall  f1-score   support
     einhorn       ...
       katze       ...
       ...
```

---

### 3. Finales Training & Visualisierung

```python
model.fit(X, y)
```

Nach der Kreuzvalidierung wird das Modell auf dem **vollständigen Datensatz** (alle 677 Samples) trainiert, das ist das Modell, das gespeichert und verwendet wird.

Anschließend werden zwei Plots erstellt und als `confusion_matrix.png` gespeichert:

```python
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

ConfusionMatrixDisplay(confusion_matrix(y, y_pred), display_labels=CLASSES).plot(
    ax=axes[0], colorbar=False, cmap="Blues"
)
axes[0].set_title("Konfusionsmatrix (10-fold CV)")

plot_tree(model, feature_names=FEATURES, class_names=CLASSES,
          filled=True, rounded=True, ax=axes[1], fontsize=9)
axes[1].set_title("Decision Tree (max_depth=5)")
```

**Linke Achse: Konfusionsmatrix:** Basiert auf den Out-of-Fold-Predictions von `cross_val_predict`, nicht auf dem finalen Modell, zeigt damit eine realistische Schätzung der Generalisierungsfähigkeit.

**Rechte Achse: Entscheidungsbaum:** Visualisiert die gelernten Entscheidungsgrenzen im `hu_0`/`hu_3`-Raum. Nützlich zur Nachvollziehbarkeit, welche Feature-Werte welche Klasse auslösen.

---

### 4. Modell speichern

```python
joblib.dump(model, OUT_PATH)
print(f"[TRAIN] Modell gespeichert: {OUT_PATH}")
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
features.csv  (677 Samples, 19 Spalten)
    └─► X [hu_0, hu_3], y [0–3]
        └─► StratifiedKFold (10 Splits)
            ├─► cross_val_score  → Accuracy pro Fold → mean ± std
            └─► cross_val_predict → y_pred (Out-of-Fold)
                └─► classification_report + ConfusionMatrixDisplay → confusion_matrix.png (links)
        └─► model.fit(X, y)  (alle 677 Samples)
            ├─► plot_tree → confusion_matrix.png (rechts)
            └─► joblib.dump → object_classifier.joblib
```

---

## Einordnung im NimSort-System

Dieses Skript steht am Anfang der ML-Kette: Es verbraucht die von einem separaten Feature-Extraktionsskript erzeugte `features.csv` und produziert `object_classifier.joblib`, das von `feature_detection.py` zur Laufzeit geladen wird. Es muss nur erneut ausgeführt werden, wenn neue Trainingsdaten vorliegen oder das Modell angepasst werden soll.