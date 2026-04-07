from abc import ABC, abstractmethod

class MainInterface(ABC):
    """State Machine Interface für NimSort Logik
    
    Verwaltet den Zustand und entscheidet basierend auf Motion- und Prediction-Daten,
    welches Target ausgeben wird.
    """
    
    @abstractmethod
    def Iprocess_motion_state(self, motion_state) -> None:
        """
        Verarbeitet den Zustand der Motion und aktualisiert internen Zustand.
        """
        pass
    
    @abstractmethod
    def Iprocess_prediction(self, prediction) -> object:
        """
        Verarbeitet Prediction von Vision.
        """
        pass
    
    @abstractmethod
    def Iget_current_state(self) -> str:
        """Gibt aktuellen State-Machine-Zustand zurück"""
        pass
    
    @abstractmethod
    def Ireset(self) -> None:
        """Setzt State Machine zurück"""
        pass

    
   