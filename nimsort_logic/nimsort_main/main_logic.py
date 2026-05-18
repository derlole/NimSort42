import threading
from enum import Enum
from nimsort_main.main_interface import MainInterface
from nimsort_vision.plausibility_check import PlausibilityCheck
from nimsort_main.process_id import ProcessId

POSITION_UNCORN= [-0.16,-0.14, 0.07] #TODO: Werte in Weltkoordinaten anpassen
POSITION_CAT= [-0.06, -0.14, 0.07]
INITIAL_POSITION = [-0.01,-0.05, 0.02]
Z_PRE_POST_PICK= 5.0 #z-Höhe über Objekt für Pick-Preposition
Z_PICK=10.0 #z-Höhe über Objekt für Pick-Position
SENTINEL = [-1.0, -1.0, -1.0,-1] 
ROBOT_REACH=-0.3 #maximale Reichweite des Roboters in x-Richtung, Werte in Weltkoordinaten anpassen

class NimSortState(Enum):
    """Enum für alle Zustände der NimSort State Machine"""
    START = "START"# Maybe nicht nötig
    INIT_CALL = "INIT_CALL"
    WAIT_FOR_INIT = "WAIT_FOR_INIT"
    GO_TO_PICKPREPOSITION = "GO_TO_PICKPREPOSITION"
    READY_FOR_PICK = "READY_FOR_PICK"
    PICK = "PICK" # TODO this state ist not used...??
    GO_TO_PICKPOSITION = "GO_TO_PICKPOSITION"
    GO_TO_DROP_CAT = "GO_TO_DROP_CAT"
    GO_TO_DROP_UNCORN = "GO_TO_DROP_UNCORN"
    DROP_UNICORN = "DROP_UNICORN"
    DROP_CAT = "DROP_CAT"
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

    def get_next_target_to_pick(self) -> tuple[float, float, float, int] | None:
        """Filtert Buffer, wählt bei mehreren gültigen Targets das mit kleinstem x."""
        if not self._prediction_buffer:
            print("[INFO][Main][GNTTP---]: Buffer leer, kein Target verfügbar.")
            return None

        # Nur Predictions innerhalb der Reichweite
        valid = [
            p for p in self._prediction_buffer
            if p.position[0] < ROBOT_REACH and p.position[0] > 0.0
            and self.plausibility_check.check_prediction(p)
        ]

        if not valid:
            print("[INFO][Main][GNTTP---]: Kein Target im Greifbereich.")
            self._prediction_buffer.clear()
            return None

        # Kleinstes x zuerst greifen
        best = min(valid, key=lambda p: p.position[0])
        self._prediction_buffer.clear()
        self.current_prediction = best

        return (
            self.current_prediction.position[0],
            self.current_prediction.position[1],
            self.current_prediction.position[2],
            self.current_prediction.object_type,
        )
                  
    
    def state_machine(self) -> tuple[float, float, float, int]:
        match self.current_state:
            case NimSortState.START:
                self.current_state = NimSortState.INIT_CALL
                return (0.0, 0.0, 0.0, ProcessId.SELF_INIT)      
            
            case NimSortState.INIT_CALL:
                self.current_state = NimSortState.WAIT_FOR_INIT  
                return (0.0, 0.0, 0.0, ProcessId.INIT_AXIS)
            
            case NimSortState.WAIT_FOR_INIT:
                if self.reached:
                    self.current_state = NimSortState.READY_FOR_PICK
                    return (0.0, 0.0, 0.0, ProcessId.INIT_AXIS)  
                 
            case NimSortState.READY_FOR_PICK:
                if self.get_next_target_to_pick() is not None:
                    self.current_state = NimSortState.GO_TO_PICKPREPOSITION
                    return (*INITIAL_POSITION, ProcessId.GO_TO_POS)

            case NimSortState.GO_TO_PICKPREPOSITION:
                if self.get_next_target_to_pick()[3] == 1 or self.get_next_target_to_pick()[3] == 2: # TODO isnt this 0 or 1?? # TODO idk, if this condition is good, we could go to the pickpre anyways, also if there is no object comming...
                    self.current_state = NimSortState.GO_TO_PICKPOSTPOSITION
                    return (self.current_prediction.position[0], self.current_prediction.position[1], Z_PRE_POST_PICK, ProcessId.GO_TO_POS) # TODO here was a 3 should be a 2, right? with enum there was a Picking drive but this should be Goto position, aint??
                       
            case NimSortState.GO_TO_PICKPOSITION:
               if self.reached and self.gripper_active:
                    self.current_state = NimSortState.GO_TO_DROP
                    return (self.current_prediction.position[0],self.current_prediction.position[1],Z_PICK, ProcessId.PICKING_DRIVE)

            case NimSortState.GO_TO_DROP_CAT:
                if self.reached and self.gripper_active and self.get_next_target_to_pick()[3] == 1: # TODO isnt this 0 or 1??
                    self.current_state = NimSortState.DROP
                    return (*POSITION_UNCORN, ProcessId.GO_TO_POS_WITH_GRIPPER)
    
            case  NimSortState.GO_TO_DROP_UNCORN:
                if self.reached and self.gripper_active and self.get_next_target_to_pick()[3] == 2: # TODO isnt this 0 or 1??
                    self.current_state = NimSortState.DROP
                    return (*POSITION_CAT, ProcessId.GO_TO_POS_WITH_GRIPPER)
                          
            case NimSortState.DROP_CAT: # TODO what are these states for??
                if self.reached and self.gripper_active:
                    self.current_state = NimSortState.READY_FOR_PICK
                    return (*POSITION_CAT, ProcessId.DEACTIVATE_GRIPPER)
            
            case NimSortState.DROP_UNICORN: # TODO what are these states for??
                if self.reached and self.gripper_active:
                    self.current_state = NimSortState.READY_FOR_PICK
                    return (*POSITION_UNCORN, ProcessId.DEACTIVATE_GRIPPER)
            
            case NimSortState.DROP:
                if self.reached and not self.gripper_active:
                    self.current_state = NimSortState.READY_FOR_PICK
                    return (*INITIAL_POSITION, ProcessId.DEACTIVATE_GRIPPER)
    
    def reset(self) -> None:
        """Setzt State Machine zurück auf START"""
        self.current_motion_state = None
        self.current_state = NimSortState.START