# nimsort_main – Hauptlogik & State Machine

## Überblick
Das `nimsort_main` Modul ist das Herzstück der Sortierlogik. Es implementiert eine State Machine, die entscheidet, wann und wo Objekte vom Band gegriffen werden sollen.

## Hauptklassen

### NimSortMain
**State Machine für die Sortierlogik**
- Verwaltet die aktuelle Bewegungsposition und den Zustand des Systems
- Entscheidet basierend auf Vision-Prediction und Plausibilitätsprüfung, ob ein Target gültig ist
- Thread-safe durch interne Locks

**Wichtige Methoden:**
- `set_current_state(motion_state)` – Setzt den aktuellen Zustand
- `get_current_state()` – Gibt aktuellen Zustand zurück
- `set_motion_state(reached, gripper_active)` – Aktualisiert Bewegungsstatus
- `predict_position(...)` – Prognostiziert Objektposition auf Basis von Vision-Daten

### NimSortState (Enum)
Definiert die möglichen Zustände der State Machine:
- `START` – Initialer Zustand
- `WAITING` – Warten auf neues Objekt
- `PICKING` – Objekt wird gegriffen
- `PLACING` – Objekt wird platziert

## Konfiguration
- Laden Sie Positionen und Parameter aus `configs.config_main`
- Wichtige Konstanten: `INITIAL_POSITION`, `POSITION_CAT`, `POSITION_UNICORN`, `ROBOT_REACH`

## Besonderheiten
- **Plausibilitätsprüfung**: Vor jedem Pick wird die vorhergesagte Position validiert (z.B. nicht außerhalb der Roboterärmreichweite)
- **Kantendetektoren**: Erkennen steigende/fallende Flanken (z.B. wenn Objekt den Sensor erreicht)
- **Thread-Safety**: Verwendung von Locks für sichere gleichzeitige Zugriffe

## Integration
1. Vision-Modul liefert Objektpositionen und Klassifikationen
2. Motion-Modul führt Roboterbewegungen durch
3. State Machine koordiniert zwischen beiden Modulen
