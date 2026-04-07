import threading
from nimsort_logic.nimsort_main.main_interface import MainInterface


class NimSortMain(MainInterface):
    """State Machine für NimSort Logik
    
    Verwaltet die aktuelle Bewegungsposition und entscheidet basierend auf
    Vision-Prediction, ob ein Target gültig ist.
    """
    
    def __init__(self):
        super().__init__()
        self.current_motion_state = None
        self.current_state = "IDLE"
        self.lock = threading.Lock()
    
    def process_motion_state(self, motion_state) -> None:
        """
        Aktualisiert die aktuelle Bewegungsposition.
        
        Args:
            motion_state: Aktuelle Position des Roboters
        """
        with self.lock:
            self.current_motion_state = motion_state
            if self.current_state == "IDLE":
                self.current_state = "MOVING"
    
    def process_prediction(self, prediction) -> object:
        """
        Verarbeitet die Prediction von Vision.
        Gibt das Target zurück wenn die Prediction zu aktueller Position passt.
        
        Args:
            prediction: Vorhersage der Vision
            
        Returns:
            Target wenn valide, None sonst
        """
        with self.lock:
            if self.current_motion_state is None:
                return None
            
            # Prüfe ob Prediction zur aktuellen Position passt
            if self._is_prediction_valid(prediction):
                self.current_state = "TARGET_FOUND"
                return self._create_target(prediction)
            else:
                self.current_state = "INVALID_PREDICTION"
                return None
    
    def _is_prediction_valid(self, prediction) -> bool:
        """
        Prüft ob die Prediction valide für aktuelle Motion ist.
        
        Args:
            prediction: Die zu prüfende Prediction
            
        Returns:
            True wenn Prediction passt, False sonst
        """
        # TODO: Implementiere die echte Validierungslogik
        # Z.B. vergleiche Positionen, Schwellenwerte etc.
        if prediction is None:
            return False
        return True
    
    def _create_target(self, prediction) -> object:
        """
        Erstellt Target aus Prediction.
        
        Args:
            prediction: Die Prediction
            
        Returns:
            Target Nachricht
        """
        # TODO: Konvertiere Prediction zu Target basierend auf Roboter-Logik
        return prediction
    
    def get_current_state(self) -> str:
        """
        Gibt aktuellen State-Machine-Zustand zurück.
        
        Returns:
            String mit aktuellem Zustand
        """
        with self.lock:
            return self.current_state
    
    def reset(self) -> None:
        """Setzt State Machine zurück auf IDLE"""
        with self.lock:
            self.current_motion_state = None
            self.current_state = "IDLE"