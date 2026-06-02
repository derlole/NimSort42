# NimSort42 – Architektur-Dokumentation

## Willkommen! 👋
Hier findest du strukturierte Dokumentation für alle Module der NimSort42-Sortierlogik.

## Module

### 1. [nimsort_main](NIMSORT_MAIN.md) – Zentrale State Machine
Die Hauptsteuerung für den Sortierablauf. Koordiniert Vision, Motion und Klassifikation.

**Kernaufgaben:**
- Entscheidung wann gegrif fen wird (State Machine)
- Validierung von Griff-Positionen
- Thread-sichere Zustandsverwaltung

**Starten Sie hier** wenn Sie verstehen möchten, wie das System funktioniert.

---

### 2. [nimsort_motion](NIMSORT_MOTION.md) – Roboterbewegung
Kontrolliert die physischen Achsen (X, Y, Z) des Roboters.

**Kernaufgaben:**
- Unabhängige Regelung pro Achse
- Sanfte Trajektorienplanung
- Position und Geschwindigkeit überwachen

**Relevant für:** Roboter-Hardware, Bewegungs-Debugging

---

### 3. [nimsort_vision](NIMSORT_VISION.md) – Bildverarbeitung
Verarbeitet Kamerabilder zur Erkennung und Lokalisierung von Objekten.

**Kernaufgaben:**
- ArUco Marker-Erkennung
- Pixel → 3D-Koordinaten Konvertierung
- Förderband-Geschwindigkeit schätzen
- Positions-Plausibilität prüfen

**Relevant für:** Kalibrierung, Vision-Debugging

---

### 4. [nimsort_feature_detection](FEATURE_DETECTION.md) – Klassifikation
Klassifiziert erkannte Objekte (z.B. Katze, Einhorn).

**Kernaufgaben:**
- Shape-Feature Extraktion (Hu-Momente)
- ML-basierte Klassifikation
- Trainieren des Klassifikators

**Relevant für:** Objekt-Erkennung, Modell-Training

---

### 5. [configs](CONFIGS.md) – Konfiguration
Zentrale Parameter für das gesamte System.

**Inhalte:**
- Roboter-Positionen und Grenzen
- Bewegungs-Parameter (Geschwindigkeit, Beschleunigung)
- Vision-Parameter (Kalibrierung, Konturgröße)
- Klassifikations-Mapping

**Wichtig:** Änderungen hier beeinflussen das gesamte System!

---

## Schnell-Übersicht: Datenfluss

```
Kamera
  ↓
Vision (nimsort_vision)
  ├─ ArUco-Markererkennung
  ├─ 3D-Position berechnen
  └─ Förderband-Geschwindigkeit schätzen
  ↓
Feature Detection (nimsort_feature_detection)
  └─ Objekt klassifizieren (Katze? Einhorn?)
  ↓
State Machine (nimsort_main)
  ├─ Position validieren (Plausibilität)
  ├─ Pick/Place Entscheidung
  └─ State aktualisieren
  ↓
Motion Control (nimsort_motion)
  └─ Bewegung ausführen
```

## Erste Schritte

**Für Entwickler:**
1. Lesen Sie zuerst [nimsort_main](NIMSORT_MAIN.md) um die Architektur zu verstehen
2. Schauen Sie sich [configs](CONFIGS.md) an für System-Parameter
3. Tauchen Sie in spezifische Module ein je nach Aufgabe

**Für Hardware-Setup:**
1. Start: [configs](CONFIGS.md)
2. Dann: [nimsort_motion](NIMSORT_MOTION.md)
3. Vision-Kalibrierung: [nimsort_vision](NIMSORT_VISION.md)

**Für Vision/Klassifikation:**
1. [nimsort_vision](NIMSORT_VISION.md)
2. [nimsort_feature_detection](FEATURE_DETECTION.md)
3. [configs](CONFIGS.md) (camera-Parameter)

---

## Wichtige Konzepte

### State Machine
Die Zentrale Logik läuft in diskreten Zuständen (START, WAITING, PICKING, PLACING, ...).
Jeder Zustand definiert Übergangsbedingungen.

### Thread-Safety
Kritische Operationen sind durch Locks geschützt, um Race Conditions zu vermeiden.

### Kalibrierung
Kamera und Roboter müssen präzise kalibriert sein. Fehlerhafte Kalibrierung führt zu Greif-Fehlern.

### Echtzeit
Die Vision und Motion arbeiten kontinuierlich. Achten Sie auf Performance-Bottlenecks!

---

## Weitere Ressourcen
- **main_logic.py** – Hauptimplementierung der State Machine
- **axis.py** – Achsen-Kontrolle im Detail
- **opencv_pipeline_aruco.py** – Vision-Implementation
- **feature_detection.py** – Klassifikator-Implementation

---

*Zuletzt aktualisiert: Juni 2026*
