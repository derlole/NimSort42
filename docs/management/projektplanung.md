## Projektplanung

### Meilensteinplan (16.03 – 29.06)

#### Bedeutung der Daten
(*Wahrscheinliches Startdatum — kann vorgezogen werden* bis *Enddatum — fix*)

1. Notwendige Koordinatensysteme festlegen (16.03 – 23.03)
- Die benötigten Koordinatensysteme für das Projekt wurden identifiziert und dokumentiert.
- Entscheidungen sind begründet dokumentiert.
- Ein Projektplan mit Meilensteinen wurde erstellt.

2. Kickoff-Präsentation mit Softwarearchitektur (24.03 – 30.03)
- Kickoff-Präsentation durchgeführt.
- Vorläufige Softwarearchitektur verabschiedet.

3. Kommunikation mit der Hardware (31.03 – 06.04)
- Hardwarekommunikation hergestellt; Nachrichten der Hardwareschnittstelle können gesendet und empfangen werden.
- Kameraaufnahmen möglich.

4. Vision-Basis und ROS-Architektur (07.04 – 13.04)
- Kamerakoordinatensystem und Ausrichtung festgelegt.
- Bildpipeline bis Kantendetektion implementiert.
- ROS-Topics (Publisher/Subscriber) implementiert und getestet.

5. Prädizierte Positionen im Weltkoordinatensystem ausgeben (14.04 – 20.04)
- Koordinatentransformationen zwischen Bezugssystemen implementiert.
- Weitergabe der Koordinaten an die Main-Node und kontinuierliche Ausgabe der vorhergesagten Position eines Objekts.

6. Initiale Kalibrierung des Gesamtsystems (21.04 – 27.04)
- Systeminitialisierung und Kalibrierung der Achsen durchgeführt.

7. Regelung zu einem Punkt im Weltkoordinatensystem (28.04 – 11.05)
- Regelung auf Zielpunkte implementiert; Achsen fahren zu kommandierten Punkten.

8. Vision-Modell fertigstellen und feinjustieren (12.05 – 25.05)
- Feature- / Shape-Matching implementiert und getestet.
- Klassifikation zuverlässig, Greifprozess implementiert.

9. Prozesslogik in Python implementiert und getestet (26.05 – 01.06)
- Daten aus Kamera, Sensorlogik etc. werden in einer State Machine zusammengeführt.

Puffer (01.06 – 15.06)

10. Finaler Test und Dokumentation (16.06 – 22.06)
- Software-Tests geschrieben.
- Praktische Tests durchgeführt.
- Dokumentation vervollständigt.

11. Abschlusspräsentationen (23.06 – 29.06)

Puffer (30.06 – 13.07)

### Meilensteine (Kurz)
1. Koordinatensysteme festgelegt (30.03)
2. Grundlagen realisiert (13.04)
3. Prädizierte Positionen verfügbar (27.04)
4. Regelung auf Punkt implementiert (25.05)
5. Prozesslogik implementiert (01.06)
6. Abschlusspräsentationen (29.06)

### Risikomanagement
- Hardwareausfall oder verspätete Bereitstellung → Verzögerungen im Zeitplan
- Ausfall eines Teammitglieds → Verzögerungen
- Unvorhergesehene Betreuungsausfälle → Bewertung gefährdet
- Eingeschränkte Hardwareverfügbarkeit → weniger Tests möglich

Maßnahme: 2 Wochen Puffer + zusätzliche Reservezeit

### Stakeholder
- Team: erfolgreiche Abgabe (Note)
- Betreuer: Durchführung der Lehrveranstaltung
- Kunde (z. B. Testkunde) – Anforderungen an Sortierfunktion

### Arbeitsweise
Iterativ, inkrementelle Entwicklung mit regelmäßigen Tests

### Hauptverantwortlichkeiten (Beispiel)
- Louis: Vision / ML-Modell
- Yannick: Prozesslogik (Main) / Position Prediction
- Benjamin: Regelung / AxisController

## Rücksprung zur [Dokumentation](../../documentation/documentation.md#13-interne-dokumentation)