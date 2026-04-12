from unittest import result

import cv2 as cv
import time
import numpy as np

from nimsort_vision.opencv_pieline_interface import OpencvPipelineInterface


class OpencvPipeline(OpencvPipelineInterface):

    def __init__(self):
        """Initialize the opencv pipeline"""
        
        self.camera_index = 4
        self.image = None
        self.timestamp = None
        self._last_result = None


    def captureImage(self):
        """Capture the image from the camera"""

        cap = cv.VideoCapture(self.camera_index)

        if not cap.isOpened():
            raise RuntimeError(f"Kamera {self.camera_index} konnte nicht geöffnet werden.")

        # Buffer leeren: mehrere Frames lesen und verwerfen
        for _ in range(5):
            cap.grab()

        # Eigentliches Bild aufnehmen
        ret, frame = cap.read()
        self.timestamp = int(time.time() * 1000)
        cap.release()

        if not ret or frame is None:
            raise RuntimeError("Bild konnte nicht aufgenommen werden.")

        self.image = frame
        
    

    def getImageData(self) -> tuple[float, float, int, np.ndarray]:
        """Verarbeitet self.image und gibt den Schwerpunkt der größten Kontur zurück.
    
        Returns:
            tuple: (cx, cy, timestamp, annotated_image)
                - cx (float): X-Koordinate des Schwerpunkts
                - cy (float): Y-Koordinate des Schwerpunkts
                - timestamp (int): Unix-Timestamp der Verarbeitung in ms
                - annotated_image (np.ndarray): Bild mit eingezeichneten Konturen"""
        
        if self.image is None:
            raise RuntimeError("Kein Bild vorhanden. Bitte zuerst captureImage() aufrufen.")

        image = self.image.copy()

        # Graustufen + Glätten + Threshold
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        blur = cv.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv.threshold(blur, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

        # Konturen finden, filtern und sortieren
        contours, _ = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        contours = [cnt for cnt in contours if cv.contourArea(cnt) >= 50]
        contours = sorted(contours, key=cv.contourArea, reverse=True)

        if not contours:
            raise RuntimeError("Keine Konturen im Bild gefunden.")

        # Größte Kontur verwenden
        contour = contours[0]

        # Schwerpunkt berechnen
        M = cv.moments(contour)
        if M["m00"] != 0:
            cx = float(M["m10"] / M["m00"])
            cy = float(M["m01"] / M["m00"])
        else:
            cx, cy = 0.0, 0.0

        # Timestamp in Millisekunden
        timestamp = int(time.time() * 1000)

        # Kontur, Schwerpunkt und Koordinaten ins Bild zeichnen
        cv.drawContours(image, [contour], -1, (0, 255, 0), 2)
        cv.circle(image, (int(cx), int(cy)), 5, (0, 0, 255), -1)
        cv.putText(image, f"({int(cx)}, {int(cy)})", (int(cx) + 10, int(cy) - 10),
                cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        
        result = (cx, cy, timestamp, image)
        self._last_result = result
        
        return cx, cy, timestamp, image

    def getLastImageData(self) -> tuple[float, float, int, np.ndarray]:
        """Get the image data from the last captured image"""
        return self._last_result