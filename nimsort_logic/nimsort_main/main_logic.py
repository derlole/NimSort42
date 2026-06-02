import threading
from nimsort_main.main_interface import MainInterface
from nimsort_vision.plausibility_check import PlausibilityCheck
from nimsort_main.process_id import ProcessId
from nimsort_vision.magic_object import MagicObject
from nimsort_main.main_states import NimSortState
from nimsort_main.edge_detector import EdgeDetectorFall, EdgeDetectorRise

from configs.config_main import INITIAL_POSITION, GENERIC_PICK_PRE_POSITION, POSITION_CAT, POSITION_UNCORN, Z_PICK, ROBOT_REACH, ZERO_ROBOT_POSITION, Z_PRE_POST_TF

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
        self.reached_edge_detector = EdgeDetectorRise()
        self.gripper_active = False
        self.plausibility_check = PlausibilityCheck()
        self._current_pickabel_object = None
        self._current_pick_pre_position = None
        self._picked = False

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
    
    def _prediction_usefull(self, x: float, y: float, z: float, object_type: int) -> bool:
        """Überprüft, ob die Prediction gültig ist und gegriffen werden kann."""
        if x < 0.0 or x > ROBOT_REACH:
            return False
        
        if not self.plausibility_check.check_position([x, y, z]):
            print(f"[WARN][Main][_PU-----]: Prediction nicht plausibel.")
            return False
        
        if self._picked:
            self._picked = False
            return False
        
        print(f"[INFO][Main][_PU-----]: picked {self._picked}")
        return True

    def set_target_to_pick(self, x: float, y: float, z: float, object_type: int) -> None:
        """Fügt eine neue Prediction zum Buffer hinzu."""
        feedback = self._prediction_usefull(x, y, z, object_type)
        if not feedback:
            return feedback
        
        new_prediction = MagicObject(
            object_type=object_type,
            position=[x, y, z],
            ts=0,  # 0 Timestampt as representation of invalid timestamp (ts is not required in Main Logic)
        )
        self._current_pickabel_object = new_prediction
        return feedback
    
    def state_machine(self) -> tuple[float, float, float, int]:
        reached_rise = self.reached_edge_detector.update(self.reached)
        
        match self.current_state:
            case NimSortState.START:
                self.current_state = NimSortState.INIT_CALL
                return (*ZERO_ROBOT_POSITION, ProcessId.SELF_INIT)      
            
            case NimSortState.INIT_CALL:
                self.current_state = NimSortState.WAIT_FOR_INIT  
                return (*ZERO_ROBOT_POSITION, ProcessId.INIT_AXIS)
            
            case NimSortState.WAIT_FOR_INIT:
                if self.reached:
                    self.current_state = NimSortState.READY_FOR_PICK
                
                return (*ZERO_ROBOT_POSITION, ProcessId.INIT_AXIS)
                 
            case NimSortState.READY_FOR_PICK:
                if self.reached:
                    self.current_state = NimSortState.GO_TO_PICKPREPOSITION
                
                return (*INITIAL_POSITION, ProcessId.GO_TO_POS)

            case NimSortState.GO_TO_PICKPREPOSITION:
                target = self._current_pickabel_object
                if target is not None and target.object_type in (0, 1) and self.reached:
                    self.current_state = NimSortState.GO_TO_PICKPOSITION
                elif target is not None and target.object_type in (0, 1):
                    self.current_state = NimSortState.GO_TO_OBJECT_PICK_PREPOSITION
                    self._current_pick_pre_position = (target.position[0] + 0.05, target.position[1], Z_PRE_POST_TF)

                return (*GENERIC_PICK_PRE_POSITION, ProcessId.GO_TO_POS)
            
            case NimSortState.GO_TO_OBJECT_PICK_PREPOSITION:
                target = self._current_pickabel_object
                if reached_rise:
                    self.current_state = NimSortState.GO_TO_PICKPOSITION
                
                return (*self._current_pick_pre_position, ProcessId.GO_TO_POS)

            
            case NimSortState.GO_TO_PICKPOSITION:
                target = self._current_pickabel_object
                if reached_rise:
                    self.current_state = NimSortState.GO_TO_PICK_POSTPOSTION
                return (self._current_pickabel_object.position[0] + 0.01, self._current_pickabel_object.position[1], Z_PICK, ProcessId.PICKING_DRIVE)
                       
            case NimSortState.GO_TO_PICK_POSTPOSTION:
                target = self._current_pickabel_object
                if reached_rise and target is not None:
                    print(f"[INFO][Main][GTPP----]: Ziel erreicht, überprüfe Target für nächsten Schritt: {target.object_type}")
                    if target.object_type == 0:
                        self.current_state = NimSortState.GO_TO_DROP_UNCORN
                    elif target.object_type == 1:
                        self.current_state = NimSortState.GO_TO_DROP_CAT
                    else: 
                        self.current_state = NimSortState.GO_TO_PICKPREPOSITION

                return (self._current_pickabel_object.position[0] + 0.01, self._current_pickabel_object.position[1], Z_PRE_POST_TF, ProcessId.PICKING_DRIVE)
            
           

            case NimSortState.GO_TO_DROP_CAT:
                target = self._current_pickabel_object
                if reached_rise and self.gripper_active and target is not None and target.object_type == 1:
                    self.current_state = NimSortState.DROP_CAT

                return (*POSITION_CAT, ProcessId.GO_TO_POS_WITH_GRIPPER)
     
            case  NimSortState.GO_TO_DROP_UNCORN:
                target = self._current_pickabel_object
                if reached_rise and self.gripper_active and target is not None and target.object_type == 0:
                    self.current_state = NimSortState.DROP_UNICORN

                return (*POSITION_UNCORN, ProcessId.GO_TO_POS_WITH_GRIPPER)
                          
            case NimSortState.DROP_CAT:
                self._current_pickabel_object = None
                if self.reached and not self.gripper_active:
                    self._picked = True
                    self.current_state = NimSortState.GO_TO_PICKPREPOSITION
                
                return (*POSITION_CAT, ProcessId.DEACTIVATE_GRIPPER)
            
            case NimSortState.DROP_UNICORN:
                self._current_pickabel_object = None
                if self.reached and not self.gripper_active:
                    self._picked = True
                    self.current_state = NimSortState.GO_TO_PICKPREPOSITION
                
                return (*POSITION_UNCORN, ProcessId.DEACTIVATE_GRIPPER)
            
    def reset(self) -> None:
        """Setzt State Machine zurück auf START"""
        self.current_motion_state = None
        self.current_state = NimSortState.START