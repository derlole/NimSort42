from enum import Enum

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