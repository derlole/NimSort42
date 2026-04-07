from abc import ABC, abstractmethod
import cv2 as cv 
import numpy as np
import matplotlib.pyplot as plt

class opencvPipelineInterface(ABC):

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