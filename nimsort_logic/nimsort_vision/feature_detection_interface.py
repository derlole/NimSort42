from abc import ABC, abstractmethod


class FeatureDetectionInterface(ABC):

    def __init__(self):
        """Initialize the Feature Detection."""
        pass

    def setImage(self, image):
        """Set the image."""
        pass

    @property
    @abstractmethod
    def getfeature():
        """Get the feature of the image."""
        pass

    def resetFeatureDetection():
        """Reset the feature detection."""
        pass