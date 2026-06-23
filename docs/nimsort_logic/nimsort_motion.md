# Inhalt

[Enums](#1-enums)
[class Controller](#2-class-controller)
[class TrajectoryPlanner](#3-class-trajectoryplanner)
[class Axis](#4-class-axis)
[class InitProcess](#5-class-initprocess)
[class SoftwareAxis](#6-class-softwareaxis)

Das Package nimsort_motion enthält insgesamt alle datien excl. der Konfigurationsdateien die für die Logik einer oder mehrerer Achsen nötig sind.

# 1 Miscellaneous
## 1.1 AxisControllerStates
Das AxisContorllerStates Enum definiert eine StateMachine, die eine Implementierung der Achsen implementieren sollte, allerdings wird das von der Logik an sich nicht überprüft.
Sie stellt den Lebenszyklus der Node oder Schnitstelle dar, welche mit der Hardware kommuniziert. 
Demnach sollte der Lebenszyklus ohne jegliche Schliefen wie folgt aussehen
```mermaid
flowchart LR
    EMP[Empty]
    INITHW[Initializing Hardware]
    INITSW[Initalizing Software]
    RUN[Running]
    RETH[Returning Home]
    SHUT[Shutdown]

    EMP -->INITHW
    INITHW -->INITSW
    INITSW -->RUN
    RUN -->RETH
    RETH -->SHUT
```

## 1.2 AxisState
Die AxisState Dataclass definiert einen einmaligen Zustand der Achse, welcher von der Axis Klasse erstellt wird. Diese dataclass dient nur der representation und der auswertung der Daten.
**Inhalt der dataclass**
```py
position: float = 0.0
velocity: float = 0.0
acceleration: float = 0.0
target_position: float = 0.0
target_reached: bool = True
```
Definition der dataclass in [axis.py](../../nimsort_logic/nimsort_motion/axis.py)

# 2 class Controller

## 2.1 Zweck

Die Klasse `Controller` implementiert einen PDF-Regler (Proportional + Differential + Feedforward) zur Ansteuerung einer einzelnen Roboterachse.

Der Regler berechnet aus der aktuellen Regelabweichung (`error`) eine Stellgröße, die von der jeweiligen Achsimplementierung zur Bewegung der Hardware verwendet werden kann.

Der Regler setzt sich aus drei Komponenten zusammen:

* **P-Anteil (Proportional):** reagiert direkt auf die aktuelle Regelabweichung.
* **D-Anteil (Differential):** reagiert auf die Änderung der Regelabweichung und verbessert das dynamische Verhalten.
* **Feedforward-Anteil:** ermöglicht die Vorsteuerung geplanter Beschleunigungen und reduziert den notwendigen Regelfehler während einer Bewegung.

Zusätzlich verfügt der Controller über:

* Begrenzung der Ausgangsgröße auf definierte Maximalwerte
* Rücksetzen interner Zustände über `reset()`
* Kalman-Filter zur Schätzung von Position und Geschwindigkeit

Die Klasse stellt ausschließlich die Regellogik bereit und besitzt keine direkte Hardwareanbindung.

## 2.2 Abhängigkeiten

| Import              | Zweck                                                                |
| ------------------- | -------------------------------------------------------------------- |
| nimsort_motion | Das eigene Package muss auf dem Zielsystem installiert sein, damit die benötigten Unterklassen und Schnittstellen importiert werden können. |

## 2.3 Nutzung

### `Controller(kp: float, kd: float, output_limit: float, kff: float)`

Konstruktor der Controller Klasse, Initialisiert ein Controller Objekt
| Parameter | Typ | Beschreibung |
|---|---|---|
| `kp` | `float` | Regelparameter des P-Anteils |
| `kd` | `float` | Regelparameter des D-Anteils |
| `kff` | `float` | Regelparameter des Feedforward-Anteils |
| `output_limit` | `float` | Maximaler wert in  +- der Ausgegeben werden kann |

**Rückgabe:** `Controller`

### `compute(error: float, dt: float, accel_ff: float = 0.0) -> float`

Methode des Reglers mit welcher ein Aktueller Reglerwert ermittelt werden kann.
| Parameter | Typ | Beschreibung |
|---|---|---|
| `error` | `float` | Fehler zwischen Ziel- und Aktuallwert |
| `dt` | `float` | vergangene Zeit seit Letztem Aufruf der Funktion |
| `accel_ff` | `float` | Beschleunigungs-Übergabewert, falls Feedforward verwendet wird |

**Rückgabe:** `float`: Berechneter Reglwert


## 2.4 Einordnung im Nimsort-System
Der Controller wird von der Axis Implementiert und nimmt für einen PDF-Regler typische Konfigurationsparameter entgegen und muss mit dem aktuellen Fehler der in der Achse berechnet wird aufgerufen. 
Der Controller ist also Teil der Achse, kann aber auch als Normaler Regler verwendet werden.

# 3 class TrajectoryPlanner

## 3.1 Zweck

Die Klasse `TrajectoryPlanner` berechnet eine Soll-Beschleunigung für eine einzelne Roboterachse auf Basis der aktuellen Bewegungssituation.

Dabei handelt es sich um einen einfachen Feedforward-Trajektorienplaner, der unter Berücksichtigung von maximaler Geschwindigkeit und maximaler Beschleunigung entscheidet, ob die Achse:

* beschleunigen,
* mit konstanter Geschwindigkeit fahren oder
* abbremsen

soll.

Der Planer erzeugt keine vollständige Trajektorie, sondern berechnet zyklisch die momentan benötigte Soll-Beschleunigung. Dadurch kann er einfach in einen Regelkreis integriert werden und dient als Vorsteuerung für den Controller.

Zusätzlich überwacht die Klasse, ob das Bewegungsziel innerhalb definierter Positions- und Geschwindigkeitstoleranzen erreicht wurde.

## 3.2 Abhängigkeiten

| Import              | Zweck                                                                |
| ------------------- | -------------------------------------------------------------------- |
| nimsort_motion | Das eigene Package muss auf dem Zielsystem installiert sein, damit die benötigten Unterklassen und Schnittstellen importiert werden können. |


## 3.3 Nutzung
### `TrajectoryPlanner(max_velocity: float, max_acceleration: float, position_tolerance: float, velocity_tolerance: float)`

Konstruktor eines TrajectoryPlanners und Konfiguration
| Parameter | Typ | Beschreibung |
|---|---|---|
| `max_velocity` | `float` | Maximale erlaubte verfahr Geschwindigkeit |
| `max_acceleration` | `float` | Maximale erlaubte Beschleunigung |
| `position_tolerance` | `float` | Toleranz wann die Position der Achse als erreicht gilt |
| `velocity_tolerance` | `float` | Toleranz wann die Geschwindigkeit der Achse für das erreichen eines Punktes langsam genug ist |

**Rückgabe:** `TrajectoryPlanner`

### `compute(target_position: float, current_position: float, current_velocity: float) -> float`

Methode mit welcher die aktuelle Sollbeschleunigung zum erreichen einer Optimalen Trajektorie gefahren werden müsste.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `target_position` | `float` | Zielposition die angefahren werden soll |
| `current_position` | `float` | Aktuelle Istposition |
| `current_velocity` | `float` | Aktuelle Istgeschwindigkeit |

**Rückgabe:** `float`: neue Sollbeschleunigung des Systems

### `property: reached`
Gibt an ob der zuletzt hinterlegte Zielpunkt erreicht ist.

**Rückgabe:** `bool`: Ob Achse den Zielpunkt erreicht hat. 

## 3.4 Einordnung im Nimsort-System
Der Trajectory Planer eröffnet der Person, welche die Achse Konfiguriert, die Möglichkeit einen PDF-Regler aus dem aktuellen PD Regler zu machen und die Notwendigen werte mittels des TrajectoryPlanners zu berechnen.

# 4 class Axis
## 4.1 Zweck

Die Klasse `Axis` repräsentiert eine einzelne Roboterachse innerhalb des Nimsort-Systems. Sie bildet die zentrale Abstraktionsschicht zwischen der Bewegungslogik und der konkreten Hardwareansteuerung.

Ihre Aufgabe besteht darin, alle für eine Achse relevanten Zustandsdaten zu verwalten und die notwendigen Bewegungsberechnungen bereitzustellen. Dazu gehören unter anderem:

* aktuelle Position, Geschwindigkeit und Beschleunigung
* Zielpositionen und Bewegungsaufträge
* Überwachung des Zielerreichungsstatus
* Berechnung und Aktualisierung des Achszustands
* Bereitstellung einer einheitlichen Schnittstelle für unterschiedliche Hardware-Implementierungen

Die Klasse implementiert dabei ein möglichst schlankes und hardwareunabhängiges Interface. Dadurch können verschiedene Achstypen oder Controller ausgetauscht werden, ohne die darüberliegende Bewegungslogik anpassen zu müssen.

Das zugehörige Interface befindet sich in [axis_interface.py](../../nimsort_logic/nimsort_motion/axis_interface.py).

## 4.2 Abhängigkeiten

| Import         | Zweck                                                                                                                                       |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| nimsort_motion | Das eigene Package muss auf dem Zielsystem installiert sein, damit die benötigten Unterklassen und Schnittstellen importiert werden können. |

## 4.3 Nutzung

### `Axis(name: str, controller:  Controller, trajectory_planner: TrajectoryPlanner, initial_position: float = 0.0)`

Konstruktor der Achs-Klasse NACH Referenzfahrt und Ruhelage im Initialpunkt
| Parameter | Typ | Beschreibung |
|---|---|---|
| `name` | `str` | Flexibler Name für die Achse |
| `controller` | `Controller` | Zugehöriger initialisierter Controller |
| `trajectory_planner` | `TrajectoryPlanner` | Zugehöriger initialisierter TrajectoryPlanner |
| `initial_position` | `float` | Initiale Position |

**Rückgabe:** `Axis`: Initialisierte Achs-Instanz

### `set_target(self, target_position: float)`
Setzen eines Neuen Zielpunktes der Achse

| Parameter | Typ | Beschreibung |
|---|---|---|
| `target_position` | `float` | Neuer Zielpunkt |

**Rückgabe:** `None`

### update(self, current_position: float, dt: float) -> float``
Neuberechnung des Outputs in einem bestimmten Zyklus

| Parameter | Typ | Beschreibung |
|---|---|---|
| `current_position` | `float` | Aktuelle Ist-position der Achse |
| `dt` | `float` | vergangene Zeit seit letztem Aufruf |

**Rückgabe:** `float`: Umzusetzende Geschwindigkeit

### `reset() -> None`
Setzt alle in der Laufzeit veränderten Werte zurück und ermöglicht einen Neustart der Achse

**Rückgabe:** `None`

### `property:position`

**Rückgabe:** `float`: letzte bekannte Ist-Position der Achse

### `property:velocity`

**Rückgabe:** `float`: letzte bekannte Ist-Geschwindigkeit der Achse

### `property:acceleration`

**Rückgabe:** `float`: letzte bekannte Ist-Beschleunigung der Achse

### `property:target_reached`

**Rückgabe:** `bool`: der erreicht status der Achse auf den zuletzt berechneten Zielpunkt

### `get_state() -> AxisState`

**Rückgabe:** `AxisState`: Aktueller Status der Achse in der statisch erzeugten dataclasss AxisState zusammengefasst

## 4.4 Einordnung im Nimsort-System
Die Klasse Axis wird in der Überklasse [SoftwareAxis](#6-class-softwareaxis) in der dreifachen ausführung implementiert um eine Portalkinematik darzustellen.
Diese können aber auch händisch erzeugt und aufgerufen werden, dabei verdreifacht sich nur der Code, da die schnitstelle genau gleich, zu der der SoftwareAxis ist.

# 5 class InitProcess

## 5.1 Zweck

Die Klasse `InitProcess` implementiert den Initialisierungs- beziehungsweise Referenzierungsprozess des Roboters.

Während der Initialisierung werden definierte Beschleunigungskommandos ausgegeben, bis festgestellt wurde, dass sich der Roboter nicht mehr bewegt. Anschließend wird die Initialisierung als abgeschlossen markiert.

Der Prozess wird typischerweise beim Systemstart oder nach einem Reset ausgeführt, um die Achsen in einen bekannten Ausgangszustand zu überführen.

Die Klasse übernimmt dabei:

* Erkennung, ob der Initialisierungsvorgang gestartet werden soll
* Ausgabe der Homing-Beschleunigungen
* Überwachung der Positionsänderungen des Roboters
* Erkennung des Stillstands
* Verwaltung des Initialisierungsstatus
* Rücksetzen des Prozesses

## 5.2 Abhängigkeiten

| Import         | Zweck                                                                                                                                       |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| nimsort_motion | Das eigene Package muss auf dem Zielsystem installiert sein, damit die benötigten Unterklassen und Schnittstellen importiert werden können. |
| configs | Das configs Package muss installiert sein, oder anders bereitgestellt werden, da die initialisierung in den Beschleunigungswerten Konfiguriert wird |
| nimsort_main | Da die Initialisierung sich nicht selbst starten darf wird der ProcessID des Main Package benötigt um diese Interpretieren zu können |  

## 5.3 Nutzung

### `InitProcess()`
Klasse zur Verwaltung und Steuerung eines Initialisierungsprozesses
| Parameter | Typ | Beschreibung |
|---|---|---|

**Rückgabe:** `InitProcess`: InitProcess Klasse 

### `should_start(process_id: int) -> bool`
Gibt an ob ein Initialisierung-Prozess gestartet werden soll.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `process_id` | `int` | Status in welcher Die Achse sich befinden soll |

**Rückgabe:** `bool`: true, wenn der Initialisierungsprozess gestartet werden soll


### `start(self, accel: tuple[float, float, float]) -> None`
Gibt die Erlaubnis eine Initialisierung zu fahren.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `accel` | `tuple[float, float, float] = HOMING_ACCELERATION` | Überschreiben der standard Beschleunigungswerte für eine Initialisierungsfahrt. |

**Rückgabe:** `None`: 

### `robot_values(self, position: tuple[float, float, float]) -> tuple[float, float, float]`
Überwachung und Koordinierung des Prozesses.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `position` | `tuple[float, float, float]` | Die Aktuellen Ist-Positionen der Achsen |

**Rückgabe:** `tuple[float, float, float]`: Beschleunigungswerte die für den Initialisierungsprozess gefahren werden sollen

### `reset() -> None`
Setzt die Initialisierung in den Leeren zustand zurück, anschließend kann die für eine erneute Initialisierung genutzt werden.

**Rückgabe:** `None`

### `is_initialized() -> bool`
Gibt zurück ob das System fertig Initialisiert ist.

**Rückgabe:** `bool`: True, wenn das System vollständig Initialisiert ist.

## 5.4 Einordnung im Nimsort-System
Die Implementierung des InitProcess erfolgt in der Beispielimplementierung in der AxisNode, äquivalent sollte an einer hardwarenahen Schnittstelle dieser InitProcess aufgerufen werden. Der InitProcess muss erst durch start gestartet werden, so kann von extern eine versehentliche initialisierung verhindert werden.
Die InitProcess Klasse zahlt also insgesamt auf die Funktionalität der Achsen ein.

# 6 class SoftwareAxis

## 6.1 Zweck

Die Klasse `SoftwareAxis` bildet die zentrale Bewegungssteuerung des Roboters auf Softwareebene.

Sie fasst die drei Einzelachsen X, Y und Z zu einer gemeinsamen Schnittstelle zusammen und koordiniert deren Bewegungen. Für jede Achse werden die notwendigen Komponenten zur Bewegungsplanung und Regelung erzeugt:

* eine Instanz von `TrajectoryPlanner`
* eine Instanz von `Controller`
* eine Instanz von `Axis`

Dadurch stellt die Klasse eine einfache API für die höheren Prozesse des Nimsort-Systems bereit, ohne dass diese direkt mit einzelnen Achsen, Reglern oder Trajektorienplanern interagieren müssen.

Zusätzlich übernimmt die Klasse:

* Transformation von Weltkoordinaten in Roboterkoordinaten
* Verteilung von Zielpositionen auf die Einzelachsen
* Zyklische Aktualisierung aller Achsen
* Verwaltung von Positionsoffsets
* Überwachung der Zielerreichung
* Prozessabhängige Auswertung des Bewegungsstatus

Die eigentliche Bewegungsplanung und Regelung wird dabei an die Klassen `Axis`, `Controller` und `TrajectoryPlanner` delegiert.

## 6.2 Abhängigkeiten

| Import              | Zweck                                                              |
| ------------------- | ------------------------------------------------------------------ |
| nimsort_motion | Das eigene Packet muss installiert sein, damit die Importe der benötigten Klassen korrekt funktioniert |
| configs | Das Konfigurationspackage muss zur Korrekten Konfiguration der Achsen installiert sein oder anders breitgestellt werden |
| nimsort_main | Die Software Achsen stellen wieder eine Logische representation dar, weswegen sie zur Interpretation der ProcessID das main_package benötigen |  

## 6.3 Nutzung
### `SoftwareAxis()`
Konstruktor der SoftwareAxis Klasse und Initialisierung der enthaltenen Einzelachsen

**Rückgabe:** `SoftwareAxis`: Instanz der Achse mit enthaltenen Axis Unterklassen

### `reached(process_id: int) -> bool`
Ermittlung ob das System gerade am gesetzten Zielpunkt steht.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `process_id` | `int` | Fahrmodus in welchem Die Achse sich befinden soll |

**Rückgabe:** `bool`: True, wenn das System am gesetzten Zielpunkt steht

### `gripper_active(process_id: int) -> bool`
Ermittelt ob der Greifer des Systems aktiv sein soll

| Parameter | Typ | Beschreibung |
|---|---|---|
| `process_id` | `int` | Fahrmodus in welchem Die Achse sich befinden soll |

**Rückgabe:** `bool`: True wenn der Greifer Aktiv sein soll

### `set_target(self, x: float , y: float , z: float) -> None`
Setzt einen neune Zielpunkt des Systems in seinen drei Achsen
| Parameter | Typ | Beschreibung |
|---|---|---|
| `x` | `float` | Zielposition der X-Achse |
| `y` | `float` | Zielposition der Y-Achse |
| `z` | `float` | Zielposition der Z-Achse |

**Rückgabe:** `None`

### `update(self, pos_x: float, pos_y:float, pos_z: float, dt: float) -> tuple[float, float, float]`
Gibt die neuen Beschleunigungswerte für die einzelnen Achsen anhand der Istposition zurück

| Parameter | Typ | Beschreibung |
|---|---|---|
| `pos_x` | `float` | Ist-Position der X-Achse |
| `pos_y` | `float` | Ist-Position der Y-Achse |
| `pos_z` | `float` | Ist-Position der Z-Achse |

**Rückgabe:** `tuple[float, float, float]`: Beschleunigungswerte der drei Achsen die gefahren werden sollen

### ` set_offset(self, x: float, y: float, z: float) -> None`
Setzt die Offsetwerte der Achsen

| Parameter | Typ | Beschreibung |
|---|---|---|
| `x` | `float` | Achsen-Offset der X-Achse |
| `y` | `float` | Achsen-Offset der Y-Achse |
| `z` | `float` | Achsen-Offset der Z-Achse |

**Rückgabe:** `None`

## 6.4 Einordnung im Nimsort-System

Die Klasse `SoftwareAxis` bildet die zentrale Schnittstelle zwischen den Prozessabläufen des Nimsort-Systems und der eigentlichen Bewegungssteuerung.

Sie verwendet intern die Klassen:

* [Axis](#4-class-axis) zur Verwaltung der Einzelachsen
* [Controller](#3-class-controller) zur Regelung
* [TrajectoryPlanner](#3-class-trajectoryplanner) zur Bewegungsplanung

und stellt diese Funktionalität als gemeinsame Steuerungseinheit für das Gesamtsystem bereit.

## Rücksprung zur [nimsort_logic](../../documentation/nimsort_logic.md#54-weitere-dokumentation)