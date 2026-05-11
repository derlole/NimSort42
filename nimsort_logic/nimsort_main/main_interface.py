from abc import ABC, abstractmethod

class MainInterface(ABC):
    """State Machine Interface für NimSort Logik
    
    Verwaltet den Zustand und entscheidet basierend auf Motion- und Prediction-Daten,
    welches Target ausgeben wird.
    """
    
    @abstractmethod
    def set_motion_state(self, reached: bool, gripper_active: bool) -> None:
        """
        Verarbeitet den Zustand der Motion und aktualisiert internen Zustand.
        """
        pass

    def set_prediction(self, prediction) -> None:
        """
        Verarbeitet Prediction von Vision.
        """
        pass

    def get_prediction(self):
        """Gibt die aktuelle Prediction zurück."""
        pass
    @abstractmethod
    def state_machine(self) -> tuple[float, float, float, int]:
        """State Machine Logik, die basierend auf aktuellen Zuständen entscheidet."""
        pass
    
    @abstractmethod
    def get_current_state(self) -> str:
        """Gibt aktuellen State-Machine-Zustand zurück"""
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Setzt State Machine zurück"""
        pass

    
   