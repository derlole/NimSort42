# 1 Inhalt

In dieser Dokumentation finden sie welche Anforderungen die Module der Logik Packages Implementieren und wo die Limitierungen dieser Liegen.
Zudem finden sie je Modul verlinkungen zu Dateien, in welchen die Nutzung, Besonderheiten oder Beispilee erklährt werden.

# 2 Modul: configs

## 2.1 Umgesetzte Anforderungen
| Anforderung | Datei |
|-----------|-----------|

## 2.2 Interfaces / Schnittstellen nach außen
- keine

## 2.3 Abstrakte Funktionen
- Halten von Konfigurationsparametern
- Zuordnung der Parameter durch verschiedene Files
- Evtl. Vorberechnung durch andere Funktionen

## 2.4 Weitere Dokumentation
- keine

# 3 Modul: nimsort_feature_detection

## 3.1 Umgesetzte Anforderungen
| Anforderung | Datei |
|-----------|-----------|
| receive preprocessed Image  | feature_detection.py |
| calculate object parameters  | feature_detection.py |
| calculate object classification with parameters  | feature_detection.py |

## 3.2 Interfaces / Schnittstellen nach außen
- FeatureDetectionInterface

## 3.3 Abstrakte Funktionen
- annehmen eines Graustufenbildes
- berechnugn von benötigten Parametern
- verarbeiten der berechneten Parameter durch Machine Learning

## 3.4 Weitere Dokumentation
- keine

# 4 Modul: nimsort_main

## 4.1 Umgesetzte Anforderungen
| Anforderung | Datei |
|-----------|-----------|
| System state machine | main_logic.py, main_states.py |
| Hold the current Object which has to be picked | main_logic.py |
| Orchestrates the drive_mode the axis | main_logic.py, process_id.py |

## 4.2 Interfaces / Schnittstellen nach außen
- MainInterface

## 4.3 Abstrakte Funktionen
- hält den aktuellen Status des Roboters
- verarbeitete alle Statusrelevanten Informationen
- Kannd den Fahrmodus der Achse vorgeben

## 4.4 Weitere Dokumentation
- keine

# 5 Modul: nimsort_motion

## 5.1 Umgesetzte Anforderungen
| Anforderung | Datei |
|-----------|-----------|
| System-initalizationprocess | init_process.py |
| hold axis data (position, velocity, acceleration) | axis.py |
| calculate acceleration form position | trajectory_planner.py |
| calculate target in the RCS  | axis.py |
| control position acceleration | controller.py |
| Absctract 3 Axis down to one with Wrapper class | software_axis.py |

## 5.2 Interfaces / Schnittstellen nach außen
- TrajectoryPlannerInterface
- InitProcessInterface
- ControllerInterface
- AxisInterface

## 5.3 Abstrakte Funktionen
- Regelung der Programmierten Achse/n auf einen Komandierten Punkt
- Anbieten eines Wrappers für drei Achsen, welche Konfiguriert werden können.
- Verarbeitung des Grippers 
- Unterschiedliche Verfahrmöglichkeiten die sich in der Definition des erreichens der Achse auszeichnen

## 5.4 Weitere Dokumentation
- keine

# 6 Modul: nimsort_vision

## 6.1 Umgesetzte Anforderungen
| Anforderung | Datei |
|-----------|-----------|
| Taking Picture | opencv_pipeline.py |
| process picture with according filters | opencv_pipeline.py |
| calculates object position | opencv_pipeline.py |
| calculate and return preprocessed Image  | opencv_pipeline.py |
| calculate and return Object position | opencv_pipeline.py |
| calculate and return conveyorbelt_speed | conveyor_speed.py |
| store received ImageData in any fitting data structure | position_prediction.py, magic_object.py |
| calculate positionPrediction for next possible MagicObject | position_prediction.py, magic_object.py |

## 6.2 Interfaces / Schnittstellen nach außen
- PositionPredictionInterface
- OpencvPipelineInterface

## 6.3 Abstrakte Funktionen
- Verarbeitung und Aufnahme von Bildern bis zu Objektpositionen und vorverarbeiteten Graustufenbildern
- Berechnung und Filterung von der Förderbandgeschwindigkeit
- Berechnung der Objekte durch timestamp letzte Position und der Berechneten Förderbandgeschwindigkeit
- Analyse für nächstes Obejkts welches gepicked werden soll.

## 6.4 Weitere Dokumentation
- keine