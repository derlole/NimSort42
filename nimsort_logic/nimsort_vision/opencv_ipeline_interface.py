from abc import ABC, abstractmethod
import cv2 as cv 
import numpy as np
import matplotlib.pyplot as plt

class opencvPipelineInterface(ABC):

    def __init__(self):
        """Initialize the pipeline"""
        pass

    def captureImage(self):
        """Capture the image from the camera"""
        pass

    @property
    @abstractmethod
    def getPosition(self):
        """Get the Position of the object"""
        pass

    @property
    @abstractmethod
    def getTimestamp(self):
        """Get the timestamp of the image"""
        pass

    def resetCv(self):
        """Reset the OpenCV pipeline"""
        pass