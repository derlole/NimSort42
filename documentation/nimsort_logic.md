# 1 Inhalt

In dieser Dokumentation finden Sie, welche Anforderungen die Module der Logik-Packages implementieren und wo die Limitierungen liegen.
Zudem finden Sie für jedes Modul Verlinkungen zu Dateien, in welchen die Nutzung, Besonderheiten und Beispiele erklärt werden.

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
- Annahme eines Graustufenbildes
- Berechnung von benötigten Parametern
- Verarbeitung der berechneten Parameter durch Machine Learning

## 3.4 Weitere Dokumentation
- [nimsort_model_trainer](../docs/nimsort_logic/model_trainer.md)
- [nimsort_feature_detection](../docs/nimsort_logic/feature_detection.md)

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
- Verwaltung des aktuellen Roboter-Status
- Verarbeitung aller Statusinformationen
- Vorgabe des Fahrmodus der Achse

## 4.4 Weitere Dokumentation
- keine

# 5 Modul: nimsort_motion

## 5.1 Umgesetzte Anforderungen
| Anforderung | Datei |
|-----------|-----------|
| System initialization process | init_process.py |
| hold axis data (position, velocity, acceleration) | axis.py |
| calculate acceleration from position | trajectory_planner.py |
| calculate target in RCS | axis.py |
| control position/acceleration | controller.py |
| abstract 3 axes into one wrapper class | software_axis.py |

## 5.2 Interfaces / Schnittstellen nach außen
- TrajectoryPlannerInterface
- InitProcessInterface
- ControllerInterface
- AxisInterface

## 5.3 Abstrakte Funktionen
- Regelung der Achsen auf einen kommandierten Punkt
- Bereitstellung eines Wrappers für drei Achsen (konfigurierbar)
- Verarbeitung des Greifers
- Verschiedene Fahrmodi mit unterschiedlichen Erreichungskriterien

## 5.4 Weitere Dokumentation
- Detaillierter Überblick der Klassen und deren Nutzung: [nimsort_motion](../docs/nimsort_logic/nimsort_motion.md)

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
- [open_cv_pipeline](../docs/nimsort_logic/open_cv_pipeline.md)