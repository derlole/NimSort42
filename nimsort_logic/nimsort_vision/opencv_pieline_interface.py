from abc import ABC, abstractmethod


class OpencvPipelineInterface(ABC):

    @abstractmethod
    def captureImage(self) -> None:
        """Capture the image from the camera"""
        pass

    @abstractmethod
    def getImageData(self) -> tuple[float, float, int, np.ndarray]:
        """Get the image data from the captured image"""
        pass

    @abstractmethod
    def getLastImageData(self) -> tuple[float, float, int, np.ndarray]:
        """Get the image data from the last captured image"""
        pass