# Inhalt

[Enums](#1-enums)
[class Axis](#2-class-axis)
[class Controller](#3-class-controller)
[class TrajectoryPlanner](#4-class-trajectoryplanner)
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

# 2 class Axis
## 2.1 Zweck
Der Zweck der Axis class ist dass diese alle daten und berechnugnen für eine Roboter Achse halten kann und dabei ein möglichst schmaled interface implementiert. Das Interface ist zu finden in [axis_interface.py](../../nimsort_logic/nimsort_motion/axis_interface.py)

## 2.2 Abhängigkeiten
| Import | Zweck |
|-------|-------|
| nimsort_motion | Das eigene Packet muss auf dem Gerät korrekt installiert sind, um die für die notwendigen unterklassen zu importieren |

## 2.3 Nutzung

## 2.4 Einordnung im Nimsort-System

# 3 class Controller

# 4 class TrajectoryPlaner

# 5 class InitProcess

# 6 class SoftwareAxis