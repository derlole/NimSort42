# configs – Konfiguration & Parameter

## Überblick
Das `configs` Modul zentralisiert alle Konstanten und Parameter der NimSort-Logik. Änderungen hier beeinflussen das gesamte System.

## Konfigurationsdateien

### config_main.py
**Zentrale Roboter- und Bewegungsparameter**

Positionen:
- `INITIAL_POSITION` – Startkalibrierposition [x, y, z] in Meter
- `GENERIC_PICK_PRE_POSITION` – Vorpositionierung vor Griff
- `POSITION_CAT` – Ablage-Position für Katzen
- `POSITION_UNCORN` – Ablage-Position für Einhörner
- `Z_PICK` – Z-Achsen-Höhe zum Greifen
- `Z_PRE_POST_TF` – Z-Höhe für Transferbewegungen

Grenzen:
- `ROBOT_REACH` – Max. Reichweite des Roboters (X-Richtung) [m]
- `ZERO_ROBOT_POSITION` – Home-Position [x, y, z]

**Verwendung:**
```python
from configs.config_main import INITIAL_POSITION, ROBOT_REACH
```

### config_motion.py
**Parameter für Achsenbewegung**
- Max-Geschwindigkeiten pro Achse [m/s]
- Beschleunigungen [m/s²]
- Getriebeübersetzungen
- Mikroschritte pro Umdrehung

### config_axis.py
**Spezifische Achsen-Kalibrierung**
- Kalibrierfaktoren pro Achse (X, Y, Z)
- Direkt-, Rückwärts- und Steuerungs-Konstanten
- Position-Offsets

### config_camera.py
**Vision & Klassifikation Parameter**
- `MIN_CONTOUR_AREA` – Minimale Größe gültiger Objekt-Konturen [Pixel²]
- `LABEL_MAP` – Mapping von Klassifikations-Indizes zu Objektnamen
  - Beispiel: `{0: "Cat", 1: "Unicorn", ...}`

### config_position_prediction.py
**Parameter für Positions-Prognose**
- Prognose-Zeitfenster
- Extrapolations-Faktoren
- Sicherheitsmargen für Kollisionsvermeidung

## Best Practices
1. **Zentrale Änderungen**: Neue Parameter hier definieren, nicht hardcodieren
2. **Kommentierung**: Immer Einheit angeben (m, m/s, rad/s, etc.)
3. **Versionskontrolle**: Alte Parameter kommentieren, nicht löschen
4. **Dokumentation**: Zusammenhang zwischen Parametern notieren

## Abhängigkeiten
- `config_main` ist die Hauptquelle für alle anderen Module
- Achsen- und Motion-Konfiguration müssen konsistent sein
- Camera-Konfiguration muss mit Vision-Pipeline synchronisiert sein

## Typ-Hints
Alle Konstanten sollten typisiert sein:
```python
ROBOT_REACH: float = 0.8  # Reichweite [m]
POSITION_CAT: List[float] = [0.5, 0.2, 0.1]  # [x, y, z] in Meter
```
