import threading
from enum import Enum
from nimsort_main.main_interface import MainInterface
from nimsort_vision.plausibility_check import PlausibilityCheck

POSTION_UNCORN= []
POSTION_CAT= []



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
        self.reached = False
        self.gripper_active = False
        self.current_prediction = None
        self.plausibility_check = PlausibilityCheck()

    def set_current_state(self, motion_state: NimSortState) -> None:
        """Setzt den aktuellen Bewegungszustand der State Machine."""
        self.current_state = motion_state

    def get_current_state(self) -> NimSortState:
        """Gibt den aktuellen Bewegungszustand der State Machine zurück."""
        return self.current_state
        
    def set_motion_state(self, reached: bool, gripper_active: bool) -> None:
        """Setzt den aktuellen Bewegungszustand der State Machine."""
        self.reached = reached
        self.gripper_active = gripper_active

    def get_next_target_to_pick(self)-> tuple[float, float, float, int]:
        """Gibt die Zielposition und Objekt-Typ zurück, wenn die Prediction gültig ist."""
        if self.current_prediction is not None and self.plausibility_check.check_prediction(self.current_prediction):
            return (self.current_prediction.position[0], self.current_prediction.position[1], self.current_prediction.position[2], self.current_prediction.object_type)
        else:
            return None
   
    
    def state_machine(self) -> tuple[float, float, float, int]:
        match self.current_state:
            case NimSortState.START:
                self.current_state = NimSortState.INIT_CALL
                return (0.0, 0.0, 0.0, 0)      
            
            case NimSortState.INIT_CALL:
                self.current_process_id = 1
                self.current_state = NimSortState.WAIT_FOR_INIT  
                return (0.0, 0.0, 0.0, 1)
            
            case NimSortState.WAIT_FOR_INIT:
                if self.reached:
                    self.current_state = NimSortState.READY_FOR_PICK
                return (0.0, 0.0, 0.0, 1)  
                 
            case NimSortState.READY_FOR_PICK:
                if self.get_next_target_to_pick() is not None:
                    self.current_state = NimSortState.GO_TO_PICKPREPOSITION
                return (-0.01, -0.01, 0.01, 2)

            case NimSortState.GO_TO_PICKPREPOSITION:
                # Zielposition für Pick vorbereiten, z.B. Annäherung an Objek
               pass
            
            case NimSortState.PICK:
                # Pick-Operation durchführen, z.B. Greifer schließen
                pass    

    
            case NimSortState.GO_TO_PICKPOSTPOSITION:
                # Nach dem Pick, Zielposition für Pick-Postion vorbereiten
                pass

            case NimSortState.GO_TO_DROP:
                # Zielposition für Drop vorbereiten, z.B. Annäherung an Sortierbehälter
                pass 
            
            case NimSortState.DROP:
                pass
    
    def reset(self) -> None:
        """Setzt State Machine zurück auf START"""
        with self.lock:
            self.current_motion_state = None
            self.current_state = NimSortState.START