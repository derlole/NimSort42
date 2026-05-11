from abc import ABC, abstractmethod


class FeatureDetectionInterface(ABC):

    def __init__(self):
        """Initialize the Feature Detection."""
        pass

    def getfeature(self, image):
        """Get the feature of the image."""
        pass

    def getLastFeature():
        """Get the last feature."""
        pass

    def resetFeatureDetection():
        """Reset the feature detection."""
        pass