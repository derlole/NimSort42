# nimsort_vision – Bildverarbeitung & Objekterkennung

## Überblick
Das `nimsort_vision` Modul verarbeitet Kamerabilder zur Erkennung und Lokalisierung von Objekten auf dem Förderband.

## Hauptklassen

### OpencvPipelineAruco
**Vision-Pipeline mit ArUco Marker-Erkennung**
- Erfasst Bilder von der Kamera
- Erkennt ArUco Marker zur Kalibrierung und Positionsbestimmung
- Konvertiert Pixel-Koordinaten in 3D-Roboterkoordinaten

**Wichtige Methoden:**
- `get_image()` – Aktuelle Kamera-Aufnahme
- `detect_markers()` – Erkennt ArUco Marker im Bild
- `pixel_to_camera(cx, cy, ...)` – Konvertiert Pixel zu 3D-Position
- `set_camera_matrix(...)` – Laden von Kamerakalibrierung

**Besonderheiten:**
- Interne Kamerakalibrierung (Kamera-Matrix, Verzeichnungskoeffizienten)
- Automatische Bildentzerrung (`_undistort()`)
- Marker-Längenkalibrierung (0,1m)

### ConveyorSpeed
**Schätzt die Geschwindigkeit des Förderbands**
- Verfolgt Objekte über mehrere Frames
- Berechnet Geschwindigkeit basierend auf Pixelbewegung
- Wichtig für genaue Positionsprognose

**Verwendung:**
```python
conveyor = ConveyorSpeed()
speed_mps = conveyor.get_speed()  # Meter pro Sekunde
```

### PlausibilityCheck
**Validiert ob Positionen physikalisch erreichbar sind**
- Prüft ob Position im Roboter-Arbeitsbereich liegt
- Überprüft Bewegungsbegrenzungen
- Verhindert unmögliche Griff-Positionen

## Konfiguration
- Kameraparameter aus `configs.config_camera`
- ArUco Marker-Größe in OpencvPipelineAruco hardcodiert (0.1m)

## Workflow
1. Kamerabild erfassen
2. ArUco Marker detektieren
3. Objektpositionen berechnen (Pixel → 3D)
4. Förderband-Geschwindigkeit schätzen
5. Zukünftige Position prognostizieren
6. Plausibilität validieren → an State Machine übergeben

## Besonderheiten
- **Kalibrierung**: Kamera-Matrix und Verzeichnung müssen genau sein
- **Bildentzerrung**: Automatisch vor Verarbeitung
- **Echtzeit**: Optimiert für Live-Bildverarbeitung vom Band
