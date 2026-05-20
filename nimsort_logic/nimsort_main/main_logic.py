import threading
from enum import Enum
from nimsort_main.main_interface import MainInterface
from nimsort_vision.plausibility_check import PlausibilityCheck
from nimsort_main.process_id import ProcessId
from nimsort_vision.magic_object import MagicObject

POSITION_UNCORN = [-0.16, -0.14, 0.07]
POSITION_CAT = [-0.06, -0.14, 0.07]
INITIAL_POSITION = [-0.01, -0.05, 0.02]
Z_PRE_POST_PICK = 0.08
Z_PICK = 0.095
GENERIC_PICK_PRE_POSITION = [-0.01, -0.05, Z_PRE_POST_PICK]
SENTINEL = [-1.0, -1.0, -1.0, -1]
ROBOT_REACH = -0.3


class NimSortState(Enum):
    START = "START"
    INIT_CALL = "INIT_CALL"
    WAIT_FOR_INIT = "WAIT_FOR_INIT"
    GO_TO_PICKPREPOSITION = "GO_TO_PICKPREPOSITION"
    READY_FOR_PICK = "READY_FOR_PICK"
    GO_TO_PICKPOSITION = "GO_TO_PICKPOSITION"
    GO_TO_DROP_CAT = "GO_TO_DROP_CAT"
    GO_TO_DROP_UNCORN = "GO_TO_DROP_UNCORN"
    DROP_UNICORN = "DROP_UNICORN"
    DROP_CAT = "DROP_CAT"
    ERROR_STATE = "ERROR_STATE"


class NimSortMain(MainInterface):
    def __init__(self):
        super().__init__()
        self.current_state = NimSortState.START
        self.reached = False
        self.gripper_active = False
        self.current_prediction: MagicObject | None = None  
        self.plausibility_check = PlausibilityCheck()

    # ── Setter ────────────────────────────────────────────────────────────────

    def set_current_state(self, state: NimSortState) -> None:
        self.current_state = state

    def get_current_state(self) -> NimSortState:
        return self.current_state

    def set_motion_state(self, reached: bool, gripper_active: bool) -> None:
        self.reached = reached
        self.gripper_active = gripper_active

    def set_target_to_pick(self, x: float, y: float, z: float, object_type: int) -> bool:
        """
        Nimmt eine neue Prediction entgegen.
        Gibt True zurück wenn akzeptiert, False wenn abgelehnt.
        Abgelehnt wird wenn: object_type ungültig, außerhalb Reichweite,
        Plausibilitätscheck fehlschlägt, oder bereits ein aktives Objekt vorhanden.
        """
        if object_type == -1:
            return False

        candidate = MagicObject(
            object_type=object_type,
            position=[x, y, z],
            ts=0.0,
        )

        if candidate.position[0] >= ROBOT_REACH:
            return False

        if not self.plausibility_check.check_prediction(candidate):
            return False

        if self.current_prediction is not None:
            return False  # bereits ein aktives Objekt → PositionPrediction warten lassen

        if candidate.object_type not in [0, 1]:
            return False
                
        self.current_prediction = candidate
        return True

    def _has_valid_target(self) -> bool:
        return self.current_prediction is not None

    def _consume_target(self) -> None:
        """Markiert das aktuelle Objekt als verarbeitet."""
        self.current_prediction = None

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
                if self.reached:
                    self.current_state = NimSortState.GO_TO_PICKPREPOSITION
                return (*INITIAL_POSITION, ProcessId.GO_TO_POS)

            case NimSortState.GO_TO_PICKPREPOSITION:
                if self._has_valid_target():
                    self.current_state = NimSortState.GO_TO_PICKPOSITION
                return (*GENERIC_PICK_PRE_POSITION, ProcessId.GO_TO_POS)

            case NimSortState.GO_TO_PICKPOSITION:
                if self.reached and self._has_valid_target():
                    obj_type = self.current_prediction.object_type
                    if obj_type == 0:
                        self.current_state = NimSortState.GO_TO_DROP_UNCORN
                    elif obj_type == 1:
                        self.current_state = NimSortState.GO_TO_DROP_CAT
                    else:
                        self._consume_target()  # ungültiger Typ → freigeben
                        self.current_state = NimSortState.GO_TO_PICKPREPOSITION

                return (
                    self.current_prediction.position[0],
                    self.current_prediction.position[1],
                    Z_PICK,
                    ProcessId.PICKING_DRIVE,
                )

            case NimSortState.GO_TO_DROP_CAT:
                if self.reached and self.gripper_active and self._has_valid_target():
                    if self.current_prediction.object_type == 1:
                        self.current_state = NimSortState.DROP_CAT
                return (*POSITION_CAT, ProcessId.GO_TO_POS_WITH_GRIPPER)

            case NimSortState.GO_TO_DROP_UNCORN:
                if self.reached and self.gripper_active and self._has_valid_target():
                    if self.current_prediction.object_type == 0:
                        self.current_state = NimSortState.DROP_UNICORN
                return (*POSITION_UNCORN, ProcessId.GO_TO_POS_WITH_GRIPPER)

            case NimSortState.DROP_CAT:
                if self.reached and self.gripper_active:
                    self._consume_target()  # Objekt gegriffen → freigeben
                    self.current_state = NimSortState.GO_TO_PICKPREPOSITION
                return (*POSITION_CAT, ProcessId.DEACTIVATE_GRIPPER)

            case NimSortState.DROP_UNICORN:
                if self.reached and self.gripper_active:
                    self._consume_target()  # Objekt gegriffen → freigeben
                    self.current_state = NimSortState.GO_TO_PICKPREPOSITION
                return (*POSITION_UNCORN, ProcessId.DEACTIVATE_GRIPPER)

    def reset(self) -> None:
        self.current_state = NimSortState.START
        self.reached = False
        self.gripper_active = False
        self.current_prediction = None