### Camera Alignment Script nutzen

1. Skript starten:
```bash
   python3 vision/camera/camera_alignment.py
```

2. Das Kamerafenster öffnet sich mit den eingeblendeten Referenzlinien.

3. Kamera physisch ausrichten, bis die relevanten Objekte mit den Referenzlinien
   übereinstimmen:
   - Das **rote Kästchen** (oben im Bild) markiert die Zielzone des 2D-Codes.
   - Die **blauen Linien** definieren die Ausrichtung zum Förderband.

4. Sobald alles passt, Kamera fixieren.  
   Die Position ist damit dokumentiert und jederzeit wiederherstellbar.

#### Steuerung

| Taste | Funktion                        |
|-------|---------------------------------|
| `ESC` | Programm beenden                |
| `F`   | Vollbild / Fenstermodus wechseln |
