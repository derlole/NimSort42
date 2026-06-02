# nimsort_feature_detection – Objekt-Klassifikation

## Überblick
Das `nimsort_feature_detection` Modul klassifiziert alle Objekte im Binärbild als verschiedene Objekttypen (z.B. Einhorn, Katze, etc.).

## Hauptklassen

### FeatureDetection
**Klassifiziert Objekte anhand von Shape-Features**
- Extrahiert Hu-Momente aus Objektkonturen
- Nutzt trainiertes ML-Modell zur Klassifikation
- Gibt Liste von Objekt-IDs für erkannte Objekte zurück

**Wichtige Methoden:**
- `get_feature(binary_image)` → List[int] – Gibt Klassifikationen zurück (z.B. [0,2,3])
- `_extract_features_for_contours(binary_image)` – Extrahiert Shape-Features

**Modell:**
- Lädt `object_classifier.joblib` (trainiertes Scikit-learn Modell)
- Wirft FileNotFoundError wenn Modell nicht vorhanden
  → **Abhilfe**: `train_classifier.py` ausführen um Modell zu generieren

**Besonderheiten:**
- **Feature-Vektor**: hu_0 + hu_3 (Hu-Momente)
- **Konturgültigkeit**: Nur Konturen mit Fläche ≥ MIN_CONTOUR_AREA werden verarbeitet
- **Sortierung**: Konturen werden nach Schwerpunkt (m10/m00) absteigend sortiert

### ModelTrainer
**Trainiert das Klassifikationsmodell**
- Nutzt Trainingsdaten von Objektbildern
- Speichert Modell als `.joblib` für FeatureDetection
- Wird offline/in Setup-Phase ausgeführt

### FeatureDetectionInterface
**Abstract Base Class für beliebige Klassifizierer**
- Ermöglicht Austausch verschiedener Implementierungen
- Definiert Schnittstelle: `get_feature(binary_image)`

## Konfiguration
- Label-Mapping in `configs.config_camera` (LABEL_MAP)
- Minimum-Konturgröße in `configs.config_camera` (MIN_CONTOUR_AREA)
- Modell-Pfad standardmäßig: `nimsort_feature_detection/object_classifier.joblib`

## Workflow
1. **Vorbereitung** (Offline): Trainig-Daten sammeln → ModelTrainer → Modell speichern
2. **Laufzeit**: FeatureDetection lädt Modell
3. **Pro Frame**: Binärbild → Konturen extrahieren → Features berechnen → Klassifikation

## Besonderheiten
- **Hu-Momente**: Rotations- und Skalierungsinvariant
- **ML-Modell**: Ermöglicht komplexere Klassifikation als einfache Schwellenwertverfahren
- **Konturgültigkeitsprüfung**: Ignoriert zu kleine Rausch-Konturen

## Fehlerbehandlung
```python
try:
    fd = FeatureDetection()  # Lädt Modell
except FileNotFoundError as e:
    print(f"Modell nicht gefunden: {e}")
    # Trainingsscript ausführen
```
