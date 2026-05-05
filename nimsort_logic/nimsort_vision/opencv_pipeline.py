import cv2 as cv
import time
import numpy as np

from nimsort_vision.opencv_pieline_interface import OpencvPipelineInterface

CAMERA_INDEX = 4
MIN_CONTOUR_AREA = 4500
ROI = (10, 113, 615, 194)  # (x, y, width, height)
Z_W_CONSTANT = 2.0

PIXEL_PUNKTE = np.array([
    [69, 62],   # Ecke 1 oben-links
    [113, 62],   # Ecke 2 oben-rechts
    [114, 109],   # Ecke 3 unten-rechts
    [70, 109],   # 1. Quadrat Ecke 4 unten-links
    [159, 61],
    [202, 61],
    [204, 107],
    [160, 108],  # 2. Quadrant unten-links
    [248, 61],
    [289, 62],
    [291, 106],
    [249, 106], # 3. Quadrant unten-links
    [493, 63],
    [529, 63],
    [529, 106],
    [494, 106],   # 6. Quadrant unten-links
    [567, 65],
    [600, 65],
    [601, 106],
    [567, 106],   # 7. Quadrant unten-links
], dtype=np.float32)

WELT_PUNKTE = np.array([
    [58, 25],   # Ecke 1 oben-links  [X_mm, Y_mm]
    [78, 25],   # Ecke 2 oben-rechts
    [78, 5],   # Ecke 3 unten-rechts
    [58, 5],   # 1. Quadrat Ecke 4 unten-links
    [98, 25],
    [118, 25], 
    [118, 5],
    [98, 5],   # 2. Quadrant unten-links
    [138, 25],
    [158, 25],
    [158, 5],
    [135, 5],   # 3. Quadrant unten-links
    [258, 25],
    [278, 25],
    [278, 5],
    [258, 5],   # 6. Quadrant unten-links
    [298, 25],
    [318, 25],
    [318, 5],
    [298, 5],   # 7. Quadrant unten-links
], dtype=np.float32)

class OpencvPipeline(OpencvPipelineInterface):

    def __init__(self):
        self.time_stamp_ms = None
        self._last_result = None
        self._test_counter = 0
        
        self._cap = cv.VideoCapture(CAMERA_INDEX)
        if not self._cap.isOpened():
            raise RuntimeError(f"Kamera {CAMERA_INDEX} konnte nicht geöffnet werden.")
        
        print(f"[OcvP][__init__]: Kamera {CAMERA_INDEX} geöffnet, warte auf Stabilisierung...")
        #time.sleep(5.0) # Wartezeit für die Kamera, um sich zu stabilisieren


        # Homographie berechnen
        self.H, _ = cv.findHomography(PIXEL_PUNKTE, WELT_PUNKTE)

        # ROI-Slice + Offset einmalig vorberechnen
        x, y, rw, rh = ROI
        self._rx = x
        self._ry = y
        self._roi_slice = (slice(y, y + rh), slice(x, x + rw))

    def pixel_zu_welt(self, u, v):
        p = np.array([u, v, 1.0])
        w = self.H @ p
        w /= w[2]
        return w[0], w[1]
    
    def captureImage(self):
        """Liest exklusiv den Rohframe – minimale Laufzeit."""
        self._test_counter += 1
        ret, self._raw_image = self._cap.read()
        self.time_stamp_ms = int(time.time() * 1000)
        cv.imwrite(f"/home/louis/Louis/Temp/raw/image_{self._test_counter}.png", self._raw_image)

        #print(f"[OcvP][captureImage]: Frame captured at {self.time_stamp_ms} ms")

        if not ret or self._raw_image is None:
            raise RuntimeError("Bildaufnahme fehlgeschlagen.")

    def getImageData(self):
        """
        Entzerrt das zuletzt aufgenommene Bild, schneidet den ROI aus
        und berechnet den Schwerpunkt der größten Kontur in Kamerakoordinaten.

        Returns:
            (X_c: float, Y_c: float, Z_c: float, timestamp: int, roi_image: np.ndarray)
        """
        #print(f"[OcvP][getImageData]: Processing image")
        if self._raw_image is None:
            raise RuntimeError("Kein Bild – zuerst captureImage() aufrufen.")
        
        roi = self._raw_image[self._roi_slice]
        cv.imwrite(f"/home/louis/Louis/Temp/roi/image_{self._test_counter}.png", roi)

        gray = cv.cvtColor(roi, cv.COLOR_BGR2GRAY)
        blur = cv.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv.threshold(blur, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

        contours, _ = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        contours = [cnt for cnt in contours if cv.contourArea(cnt) >= MIN_CONTOUR_AREA]
        contours = sorted(contours, key=lambda cnt: cv.moments(cnt)["m10"] / cv.moments(cnt)["m00"], reverse=True)
        
        if not contours:
            raise RuntimeError("Keine Konturen im ROI gefunden.")
            #print("[OcvP][getImage]: Keine Konturen im ROI gefunden.")

        contour = contours[0]

        M = cv.moments(contour)
        if M["m00"] != 0:
            cx_roi = float(M["m10"] / M["m00"])
            cy_roi = float(M["m01"] / M["m00"])
        else:
            cx_roi, cy_roi = 0.0, 0.0

        cx_px = cx_roi + self._rx
        cy_px = cy_roi + self._ry

        X_w, Y_w = self.pixel_zu_welt(cx_px, cy_px)
        print(f"[OcvP][getImageData]: Detected object at pixel ({cx_px:.1f}, {cy_px:.1f}) -> world ({X_w:.1f}, {Y_w:.1f})")
        result = (X_w, -Y_w, Z_W_CONSTANT, self.time_stamp_ms, roi) #ACHTUNG: Y-Wert wird negiert, da in Weltkoordinaten die positive Y-Achse einen Vorzeichen wechsel hat.
        self._last_result = result
        return result

    def getLastImageData(self):
        """Get the image data from the last captured image"""
        return self._last_result

    def release(self):
        if self._cap.isOpened():
            self._cap.release()