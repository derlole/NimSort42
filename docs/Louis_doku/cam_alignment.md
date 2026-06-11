# `camera_alignment.py` -- Kamera-Ausrichtungshilfe

## Zweck

Dieses Skript dient der **visuellen Ausrichtung der Förderbandkamera**. Es öffnet einen Live-Videostream und zeichnet fest definierte Hilfslinien ins Bild, mit denen die Kamera physisch so ausgerichtet werden kann, dass sie exakt auf die ROI-Grenzen des NimSort-Förderbands zeigt.

Die beiden **blauen horizontalen Linien** markieren die obere und untere Förderbandkante, und ein **roter Rahmen** markiert den Referenzberich auf dem 2D-Code des oberen Rand des Bandes.

---

## Abhängigkeiten


| Name | Version |
|------|---------|
| Opencv-python | 4.13.0 |

---

## Konfiguration: Hilfslinien

```python
lines = [
    ((566, 107), (375, 107), (0, 0, 255), 1),  # roter Rahmen: untere Kante
    ((375, 107), (374,  60), (0, 0, 255), 1),  # roter Rahmen: linke Kante
    ((374,  60), (566,  63), (0, 0, 255), 1),  # roter Rahmen: obere Kante
    ((566,  63), (566, 107), (0, 0, 255), 1),  # roter Rahmen: rechte Kante
    ((23,  307), (600, 275), (255, 0, 0), 2),  # blau: untere ROI-Grenze
    ((16,  118), (566, 112), (255, 0, 0), 2),  # blau: obere ROI-Grenze
]
```

Jeder Eintrag ist ein Tupel der Form `(start_px, end_px, farbe_BGR, dicke_px)`.

| Linie | Farbe | Bedeutung |
|-------|-------|-----------|
| Linien 1–4 | Rot | Rechteckiger Rahmen um den 2D-Code |
| Linie 5 | Blau | Untere Begrenzung der Förderband-ROI |
| Linie 6 | Blau | Obere Begrenzung der Förderband-ROI |

> Die blauen Linien verlaufen leicht schräg zeueinander, weil die Kamera **nicht** senkrecht von oben auf das Förderband zeigt sondern schräg von Forne zum Förderband ausgerichtet ist. 

---

## Hauptschleife

```python
while True:
    ret, frame = cap.read()
    if not ret:
        break

    for (start, end, color, thickness) in lines:
        cv2.line(frame, start, end, color, thickness)

    cv2.imshow("FBI-Survailance-Cam", frame)
```

Pro Frame wird jede Hilfslinie direkt ins Bild gezeichnet (`cv2.line`) und dann angezeigt. Das Original-Frame wird dabei nicht verändert. Die Linien existieren nur im Anzeigebild.

---

## Tastatursteuerung

| Taste | Aktion |
|-------|--------|
| `ESC` | Programm beenden |
| `f` | Vollbild umschalten (toggle zwischen `WINDOW_FULLSCREEN` und `WINDOW_NORMAL`) |

---

## Nutzung

```bash
python config_camera.py
```

Kamera-Index `4` ist fest kodiert (`cv2.VideoCapture(4)`). Falls die Kamera unter einem anderen Index läuft, muss dieser angepasst werden. Das Fenster ist resizable (`cv2.WINDOW_NORMAL`), sodass es auch auf kleineren Monitoren nutzbar bleibt.

---

## Einordnung im NimSort-System

Dieser Code gehört zur **Kamera-Ausrichtung**, der vor dem eigentlichen Pipeline-Betrieb ausgeführt wird.