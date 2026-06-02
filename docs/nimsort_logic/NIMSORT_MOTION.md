# nimsort_motion – Roboterbewegung & Achsenkontrolle

## Überblick
Das `nimsort_motion` Modul steuert die physischen Achsen des Roboters. Jede Achse (X, Y, Z) wird unabhängig kontrolliert mit eigener Trajektorienplanung und Regelung.

## Hauptklassen

### Axis
**Verwaltet eine einzelne Roboter-Achse**
- Enthält Positionsdaten und Zustandsinformationen
- Kommuniziert mit dem Motion-Controller
- Nutzt Trajektorienplaner für sanfte Bewegungen

**Wichtige Methoden:**
- `set_target_position(position)` – Setzt Zielposition
- `get_current_state()` → AxisState – Gibt aktuellen Status zurück
- `move()` – Führt geplante Bewegung durch

### Controller
**Niederebenen-Kontrolle einer Achse**
- Berechnet und sendet Steuersignale an den Antrieb
- Lädt/speichert Konfiguration (Max-Geschwindigkeit, Beschleunigung, etc.)

### TrajectoryPlanner
**Plant glatte Bewegungstrajektorien**
- Berechnet Positionsprofile, die angeforderte Ziele erreichen
- Berücksichtigt Geschwindigkeits- und Beschleunigungsgrenzen

### AxisState (Dataclass)
**Snapshot des Achsenzustands für Logging/Debugging**
- `position` – Aktuelle Position relativ zu Home [m]
- `velocity` – Aktuelle Geschwindigkeit [m/s]
- `acceleration` – Ziel-Beschleunigung [m/s²]
- `target_position` – Aktuelles Ziel [m]
- `target_reached` – Boolean, ob Ziel erreicht wurde

## Konfiguration
- Controller-Limits kommen aus `configs.config_axis`
- Initialpositionen und Roboter-Reichweite aus `configs.config_main`

## Besonderheiten
- **Unabhängige Achsenregelung**: Jede Achse läuft autonom, koordiniert durch State Machine
- **Sanfte Bewegungen**: Trajektorienplaner verhindert ruckartige Bewegungen
- **Diagnostik**: AxisState ermöglicht detailliertes Logging für Debugging

## Integration
1. State Machine fordert Bewegungen an → Controller setzt Zielposition
2. Axis-Objekt berechnet Position und Zustand
3. TrajectoryPlanner erzeugt glatte Kurven
4. Hardware erhält finale Steuersignale
