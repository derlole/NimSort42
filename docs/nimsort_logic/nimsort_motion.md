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

### Einfaches Beispiel

```python
from nimsort_motion.controller import Controller

controller = Controller(
    kp=20.0,
    kd=2.0,
    output_limit=100.0,
    kff=0.5
)

target_position = 100.0
current_position = 85.0

dt = 0.01

error = target_position - current_position

control_output = controller.compute(
    error=error,
    dt=dt,
    accel_ff=0.0
)

print(control_output)
```

### Typischer Einsatz innerhalb eines Regelkreises

```python
controller = Controller(
    kp=20.0,
    kd=2.0,
    output_limit=100.0
)

while True:
    current_position = axis.position
    target_position = trajectory.position

    error = target_position - current_position

    control_signal = controller.compute(
        error=error,
        dt=cycle_time
    )

    axis.set_control_output(control_signal)
```

### Rücksetzen des Reglers

```python
controller.reset()
```

Dies setzt interne Zustände wie den gespeicherten Fehler zurück und sollte beispielsweise nach einer Referenzfahrt oder beim Neustart einer Bewegung erfolgen.

## 2.4 Einordnung im Nimsort-System
Der Controller wird von der Axis Implementiert und nimmt für einen PDF-Regler typische Konfigurationsparameter entgegen und muss mit dem aktuellen Fehler der in der Achse berechnet wird aufgerufen. 
Der Controlle ist also Teil der Achse, kann aber auch als Normaler Regler verwendet werden.

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

### Einfaches Beispiel

```python id="3bgq4r"
planner = TrajectoryPlanner(
    max_velocity=1.0,
    max_acceleration=2.0,
    position_tolerance=0.001,
    velocity_tolerance=0.01
)

target_position = 0.5
current_position = 0.1
current_velocity = 0.0

target_acceleration = planner.compute(
    target_position=target_position,
    current_position=current_position,
    current_velocity=current_velocity
)


```

### Typischer Einsatz innerhalb einer Bewegungssteuerung

```python id="3m8j1r"
    # cyclically called code e.g trough callbacks

    target_acceleration = planner.compute(
        target_position=target_position,
        current_position=axis.position,
        current_velocity=axis.velocity
    )

    control_signal = controller.compute(
        error=target_position - axis.position,
        dt=cycle_time,
        accel_ff=target_acceleration
    )

```

### Überprüfung der Zielerreichung

```python id="vprkfe"
if planner.reached:
    print("Zielposition erreicht")
```

Der Status wird automatisch während jedes Aufrufs von `compute()` aktualisiert.

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

### Einfaches Beispiel

```python
from nimsort_motion.axis import Axis

# Achse erzeugen
axis = Axis(...)

# Zielposition setzen
axis.set_target_position(250.0)

# Zyklischer Aufruf der Achslogik
while not axis.state.target_reached:
    axis.update()

    state = axis.state

    print(
        f"Position: {state.position:.2f}, "
        f"Geschwindigkeit: {state.velocity:.2f}"
    )

# Ziel erreicht
print("Bewegung abgeschlossen")
```

### Typischer Ablauf innerhalb einer Steuerung

```text
1. Achse initialisieren
2. Referenzfahrt durchführen
3. Zielposition vorgeben
4. Achslogik zyklisch aufrufen
5. Achszustand auswerten
6. Auf target_reached warten
7. Nächsten Bewegungsauftrag ausführen
```

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
| configs | Das configs Package mus installiert sein, oder anders bereitgestellt werden, da die initialisierung in den Beschleunigungswerten Konfiguriert wird |
| nimsort_main | Da die Initialisierung sich nicht selbst starten darf wird der ProcessID des Main Package benötigt um diese Interpretieren zu können |  

## 5.3 Nutzung

### Starten des Initialisierungsvorgangs

```python
from nimsort_motion.init_process import InitProcess

process = InitProcess()

process.start()
```

### Prozess zyklisch ausführen

```python
while not process.is_initialized():

    current_position = (
        robot.x,
        robot.y,
        robot.z
    )

    acceleration_command = process.robot_values(
        current_position
    )

    robot.set_acceleration(
        acceleration_command
    )
```

### Start über ProcessId prüfen

```python
if process.should_start(process_id):
    process.start()
```

### Initialisierung zurücksetzen

```python
process.reset()
```

### Initialisierungsstatus abfragen

```python
if process.is_initialized():
    print("Robot initialization completed")
```

### Typischer Ablauf

```text
1. Initialisierungsprozess erzeugen
2. Startbedingung prüfen
3. Prozess starten
4. Positionsdaten zyklisch übergeben
5. Homing-Beschleunigung ausgeben
6. Stillstand des Roboters erkennen
7. Initialisierung als abgeschlossen markieren
8. In den normalen Betriebsmodus wechseln
```

## 5.4 Einordnung im Nimsort-System
Die Implementierung des InitProcess erfolgt in der Beispielimplementierung in der AxisNode, äquivalent sollte an einer hardwarenahen Schnittstelle dieser InitProcess aufgerufen werden. Der initProcess mus erst durch start gestartet werden, so kann von extern eine versehentliche initialisierung verhindert werden.
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

### Instanz erzeugen

```python
software_axis = SoftwareAxis()
```

### Zielposition vorgeben

```python
software_axis.set_target(
    x=0.25,
    y=0.10,
    z=-0.15
)
```

Die Zielkoordinaten werden automatisch vom Weltkoordinatensystem in das Roboterkoordinatensystem transformiert und anschließend an die einzelnen Achsen übergeben.

### Zyklische Aktualisierung

```python
while True:

    acc_x, acc_y, acc_z = software_axis.update(
        pos_x=current_x,
        pos_y=current_y,
        pos_z=current_z,
        dt=cycle_time
    )

    robot.send_acceleration(
        acc_x,
        acc_y,
        acc_z
    )
```

### Zielerreichung prüfen

```python
if software_axis.reached(process_id):
    print("Target reached")
```

Abhängig vom aktiven Prozess werden unterschiedliche Achsen zur Bewertung der Zielerreichung berücksichtigt.

### Positionsoffset setzen

```python
software_axis.set_offset(
    x=offset_x,
    y=offset_y,
    z=offset_z
)
```

Offsets werden bei der Positionsrückführung berücksichtigt und können beispielsweise nach einer Initialisierung oder Referenzierung gesetzt werden.

### Greiferstatus bestimmen

```python
if software_axis.gripper_active(process_id):
    activate_gripper()
```

## 6.4 Einordnung im Nimsort-System

Die Klasse `SoftwareAxis` bildet die zentrale Schnittstelle zwischen den Prozessabläufen des Nimsort-Systems und der eigentlichen Bewegungssteuerung.

Sie verwendet intern die Klassen:

* [Axis](#4-class-axis) zur Verwaltung der Einzelachsen
* [Controller](#3-class-controller) zur Regelung
* [TrajectoryPlanner](#3-class-trajectoryplanner) zur Bewegungsplanung

und stellt diese Funktionalität als gemeinsame Steuerungseinheit für das Gesamtsystem bereit.

