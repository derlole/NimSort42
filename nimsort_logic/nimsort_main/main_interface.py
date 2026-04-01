from abc import ABC, abstractmethod
from dataclasses import dataclass




@dataclass
class Point:
    x: float
    y: float
    z: float

@dataclass
class NimSortPrediction:
    predicted_position_wcs: Point
    object_type: int

@dataclass
class NimSortTarget:
    target_point: Point
    process_id: int

@dataclass
class NimSortMotionState:
    reached: bool
    gripper_active: bool




class INimSortPrediction(ABC):
    @abstractmethod
    def publish_prediction(self, msg: NimSortPrediction) -> None:
        pass

    @abstractmethod
    def on_prediction_received(self, msg: NimSortPrediction) -> None:
        pass


class INimSortTarget(ABC):
    @abstractmethod
    def publish_target(self, msg: NimSortTarget) -> None:
        pass

    @abstractmethod
    def on_target_received(self, msg: NimSortTarget) -> None:
        pass


class INimSortMotionState(ABC):
    @abstractmethod
    def publish_motion_state(self, msg: NimSortMotionState) -> None:
        pass

    @abstractmethod
    def on_motion_state_received(self, msg: NimSortMotionState) -> None:
        pass


# --- MainNode Interface ---

class IMainNode(INimSortPrediction, INimSortTarget, INimSortMotionState):
    """
    Zentraler Hub – implementiert alle Pub/Sub-Interfaces.
    """
    pass


# --- MainLogic Interface ---

class IMainLogic(ABC):
    @abstractmethod
    def set_main_node(self, node: IMainNode) -> None:
        pass

    @abstractmethod
    def run(self) -> None:
        pass