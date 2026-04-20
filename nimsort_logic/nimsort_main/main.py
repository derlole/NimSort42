import threading
from enum import Enum
from nimsort_main.main_interface import MainInterface


class NimSortState(Enum):
    """Enum für alle Zustände der NimSort State Machine"""
    START = "START"
    INIT_CALL = "INIT_CALL"
    WAIT_FOR_INIT = "WAIT_FOR_INIT"
    GO_TO_PICKPREPOSITION = "GO_TO_PICKPREPOSITION"
    READY_FOR_PICK = "READY_FOR_PICK"
    PICK = "PICK"
    GO_TO_PICKPOSTPOSITION = "GO_TO_PICKPOSTPOSITION"
    GO_TO_DROP = "GO_TO_DROP"
    DROP = "DROP"
    ERROR_STATE = "ERROR_STATE"


class NimSortMain(MainInterface):
    """State Machine für NimSort Logik
    
    Verwaltet die aktuelle Bewegungsposition und entscheidet basierend auf
    Vision-Prediction, ob ein Target gültig ist.
    """
    
    def __init__(self):
        super().__init__()
        self.current_motion_state = None
        self.current_state = NimSortState.START
        self.lock = threading.Lock()
    
    def process_motion_state(self, motion_state) -> None:
        """
        Aktualisiert die aktuelle Bewegungsposition.
        
        Args:
            motion_state: Aktuelle Position des Roboters
        """
        with self.lock:
            self.current_motion_state = motion_state
            if self.current_state == NimSortState.START:
                self.current_state = NimSortState.INIT_CALL
    
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
                self.current_state = NimSortState.ERROR_STATE
                return None
            
            # Prüfe ob Prediction zur aktuellen Position passt
            if self._is_prediction_valid(prediction):
                self.current_state = NimSortState.READY_FOR_PICK
                return self._create_target(prediction)
            else:
                self.current_state = NimSortState.ERROR_STATE
                return None
    
    
    def _create_target(self, prediction) -> object:
        """
        Erstellt Target aus Prediction.
        
        Args:
            prediction: Die Prediction
            
        Returns:
            Target Nachricht
        """
      
        return prediction
    
    def get_current_state(self) -> NimSortState:
        """
        Gibt aktuellen State-Machine-Zustand zurück.
        
        Returns:
            NimSortState Enum mit aktuellem Zustand
        """
        with self.lock:
            return self.current_state
    
    def transition_to(self, next_state: NimSortState) -> None:
        """
        Wechselt zu einem neuen Zustand.
        
        Args:
            next_state: Der nächste Zustand (NimSortState Enum)
        """
        with self.lock:
            print(f"[INFO]: State Transition: {self.current_state.value} -> {next_state.value}")
            self.current_state = next_state
    
    def reset(self) -> None:
        """Setzt State Machine zurück auf START"""
        with self.lock:
            self.current_motion_state = None
            self.current_state = NimSortState.START