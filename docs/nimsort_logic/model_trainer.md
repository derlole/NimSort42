# `model_trainer.py` -- Klassifikatortraining für NimSort

## Zweck

Dieses Skript trainiert den Objektklassifikator. Es liest extrahierte Features aus `features.csv`, bewertet ein `DecisionTreeClassifier`-Modell per stratifizierter Kreuzvalidierung und speichert das finale Modell als `.joblib`-Datei, bereit zum Laden durch `feature_detection.py`.

Das Skript ist kein importierbares Modul, sondern wird einmalig manuell ausgeführt, wenn Trainingsdaten vorliegen oder das Modell neu trainiert werden soll.

---

## Abhängigkeiten

| Name | Version |
|------|---------|
| numpy | 1.26.0+ |
| joblib | 1.3.0+ |
| pandas | 2.0.0+ |
| matplotlib | 3.7.0+ |
| scikit-learn | 1.3.0+ |



---

## Pfade & Konfiguration

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

- Lädt den Datensatz aus der CSV-Datei (CSV_PATH) in einen Pandas DataFrame.
- Extrahiert die in FEATURES definierten Spalten (also `hu_0` und `hu_3`) als Feature-Matrix `X, konvertiert zu float32.
- Wandelt die textuellen Labels (df["label"]) in numerische Klassenindizes um, indem für jedes Label die Position in CLASSES gesucht wird (einhorn→0, katze→1, kreis→2, quadrat→3)-
- Grund für die Umwandlung: DecisionTreeClassifier benötigt numerische Targets statt Strings
- Gibt zur Kontrolle aus, wie viele Samples geladen wurden und welche Features verwendet werden (hier: 677 Zeilen, Features hu_0/hu_3)

---

### 2. Modell & Kreuzvalidierung

- Erstellt einen `DecisionTreeClassifier` mit maximaler Baumtiefe 5 (`max_depth=5`), begrenzt die Komplexität, um Overfitting zu vermeiden.
- `random_state=1` macht das Modell reproduzierbar (gleiche Zufallsentscheidungen bei jedem Lauf).
- Definiert eine stratifizierte 10-fache Kreuzvalidierung (`StratifiedKFold`, `n_splits=10`).
- Stratifiziert bedeutet: Jede Klasse ist in jedem Fold proportional zur Gesamtverteilung vertreten, wichtig bei leicht ungleicher Klassenverteilung.
- `shuffle=True` mischt die Daten vor dem Aufteilen, `random_state=1` macht auch das reproduzierbar.
- `cross_val_score`: trainiert und testet das Modell über alle 10 Folds, liefert die Accuracy  zurück.
- `cross_val_predict`: liefert für jedes Sample die Vorhersage aus dem Fold, in dem es als Testdaten verwendet wurde (Out-of-Fold-Predictions), wird typischerweise für die Konfusionsmatrix benötigt, da damit jede Vorhersage auf "ungesehenen" Daten basiert.

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

- Trainiert das finale Modell mit `model.fit(X, y)` auf dem **gesamten Datensatz** (alle 677 Samples), dieses Modell wird später gespeichert.
- Linker Plot: Konfusionsmatrix
  - Berechnet aus den Out-of-Fold-Predictions (`y_pred`) der Kreuzvalidierung vs. den wahren Labels (`y`).
  - Zeigt also die Performance auf "ungesehenen" Daten, nicht die (optimistischere) Performance des finalen, auf allen Daten trainierten Modells.
  - Achsenbeschriftung mit den Klassennamen (`CLASSES`), Farbschema Blau, ohne Farbskala (`colorbar=False`).
- Rechter Plot: Visualisierung des trainierten Decision Trees (`plot_tree`)
  - Zeigt die Baumstruktur mit Feature-Namen, Klassennamen, farblich gefüllten und abgerundeten Knoten.
  - Achtung: zeigt den auf **allen** Daten trainierten Baum (`model`), nicht einen der CV-Folds.
- Beide Plots werden mit Titeln versehen und am Ende als Datei `confusion_matrix.png` gespeichert.

**Linke Achse: Konfusionsmatrix:** Basiert auf den Out-of-Fold-Predictions von `cross_val_predict`, nicht auf dem finalen Modell, zeigt damit eine realistische Schätzung der Generalisierungsfähigkeit.

**Rechte Achse: Entscheidungsbaum:** Visualisiert die gelernten Entscheidungsgrenzen im `hu_0`/`hu_3`-Raum. Nützlich zur Nachvollziehbarkeit, welche Feature-Werte welche Klasse auslösen.

---

### 4. Modell speichern

- Speichert das finale, trainierte Modell mittels `joblib.dump()` unter dem Pfad `OUT_PATH` (Dateiname: `object_classifier.joblib`)
- `joblib` ist für die Serialisierung von scikit-learn-Modellen optimiert (effizienter als z. B. `pickle` bei NumPy-Arrays)
- Gibt eine Bestätigung mit dem Speicherpfad aus
- Diese gespeicherte Datei wird später von `feature_detection.py` beim Programmstart geladen, um Vorhersagen zu treffen, ohne das Modell erneut trainieren zu müssen

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