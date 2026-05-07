import cv2 as cv
import time
import numpy as np
import os

from nimsort_vision.opencv_pieline_interface import OpencvPipelineInterface
from nimsort_vision.plausibility_check import PlausibilityCheck

CAMERA_INDEX = 4
MIN_CONTOUR_AREA = 4500
Z_W_CONSTANT_IN_MM = 2.0
THRESHOLD = 130.05

# Trapez-ROI: vier Eckpunkte im Uhrzeigersinn (oben-links, oben-rechts, unten-rechts, unten-links)
ROI_TRAPEZ = np.array([
    [14,  121],   # oben-links
    [602, 116],   # oben-rechts
    [602, 272],   # unten-rechts
    [14,  304],   # unten-links
], dtype=np.int32)

PIXEL_PUNKTE = np.array([
    [66, 131],   # Ecke 1 oben-links
    [109, 131],  # Ecke 2 oben-rechts
    [109, 178],  # Ecke 3 unten-rechts
    [66, 178],   # Ecke 4 unten-links
    [153, 129],  # 2. Quadrat oben-links
    [195, 129],
    [195, 175],
    [153, 176], 
    [238, 128],  # 3. Quadrat oben-links
    [278, 127],
    [279, 173],
    [239, 174], 
    [321, 127],   # 4. Quadrat oben-links
    [359, 127],
    [360, 172],
    [321, 172],  
    [400, 126],   # 5. Quadrat oben-links
    [437, 126],
    [438, 170],
    [401, 172],  
                  # 6. Quadrat oben-links
], dtype=np.float32)

WELT_PUNKTE = np.array([
    [59, 0],      # Ecke 1 oben-links  [X_mm, Y_mm]
    [78.40, 0],   # Ecke 2 oben-rechts
    [78.40, -20], # Ecke 3 unten-rechts
    [59, -20],    # Ecke 4 unten-links
    [97.7, 0],    # 2. Quadrat oben-links
    [117.18, 0],
    [117.18, -20],
    [97.7, -20],   
    [136.3, 0],   # 3. Quadrant oben-links
    [155.8, 0],
    [155.8, -20],
    [136.3, -20], 
    [175.1, 0],    # 4. Quadrant oben-links
    [194.3, 0],
    [194.3, -20],
    [175.1, -20],  
    [213.8, 0],    # 5. Quadrant oben-links
    [233.3, 0],
    [233.3, -20],
    [213.8, -20],  
                  # 6. Quadrant oben-links
], dtype=np.float32)


class OpencvPipeline(OpencvPipelineInterface):

    def __init__(self):
        self.time_stamp_ms = None
        self._last_result = None
        self._test_counter = 0
        self._plausi = PlausibilityCheck()

        # Basisverzeichnis für Bilder relativ zum Skript-Verzeichnis
        self._base_images_dir = os.path.join(os.path.dirname(__file__), "..", "images_live")
        os.makedirs(os.path.join(self._base_images_dir, "raw"), exist_ok=True)
        os.makedirs(os.path.join(self._base_images_dir, "roi"), exist_ok=True)
        os.makedirs(os.path.join(self._base_images_dir, "bin"), exist_ok=True)

        self._cap = cv.VideoCapture(CAMERA_INDEX)
        if not self._cap.isOpened():
            raise RuntimeError(f"Kamera {CAMERA_INDEX} konnte nicht geöffnet werden.")

        print(f"[OcvP][__init__]: Kamera {CAMERA_INDEX} geöffnet, warte auf Stabilisierung...")

        # Homographie berechnen
        self.H, _ = cv.findHomography(PIXEL_PUNKTE, WELT_PUNKTE)

        # Bounding Box des Trapezes einmalig vorberechnen (für effizienten Slice)
        x, y, w, h = cv.boundingRect(ROI_TRAPEZ)
        self._rx = x
        self._ry = y
        self._roi_slice = (slice(y, y + h), slice(x, x + w))

        # Trapez-Maske relativ zur Bounding Box vorberechnen
        trapez_shifted = ROI_TRAPEZ - np.array([x, y], dtype=np.int32)
        self._trapez_mask = np.zeros((h, w), dtype=np.uint8)
        cv.fillPoly(self._trapez_mask, [trapez_shifted], 255)

    def pixel_zu_welt(self, u, v):
        p = np.array([u, v, 1.0])
        w = self.H @ p
        w /= w[2]
        return w[0], w[1]
    
    def convert(self, x_mm, y_mm, z_mm):
        x_m = x_mm / 1000.0
        y_m = y_mm / 1000.0
        z_m = z_mm / 1000.0
        return x_m, y_m, z_m

    def captureImage(self):
        """Liest exklusiv den Rohframe – minimale Laufzeit."""
        self._test_counter += 1
        ret, self._raw_image = self._cap.read()
        self.time_stamp_ms = int(time.time() * 1000)
        cv.imwrite(os.path.join(self._base_images_dir, "raw", f"image_{self._test_counter}.png"), self._raw_image)

        if not ret or self._raw_image is None:
            raise RuntimeError("Bildaufnahme fehlgeschlagen.")

    def getImageData(self):
        """
        Entzerrt das zuletzt aufgenommene Bild, maskiert das Trapez-ROI
        und berechnet den Schwerpunkt der größten Kontur in Weltkoordinaten.
        """
        if self._raw_image is None:
            raise RuntimeError("Kein Bild – zuerst captureImage() aufrufen.")

        # Bounding-Box-Ausschnitt + Trapezmaske anwenden
        roi = self._raw_image[self._roi_slice].copy()
        roi_masked = cv.bitwise_and(roi, roi, mask=self._trapez_mask)
        cv.imwrite(os.path.join(self._base_images_dir, "roi", f"image_{self._test_counter}.png"), roi_masked)

        gray = cv.cvtColor(roi_masked, cv.COLOR_BGR2GRAY)
        blur = cv.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv.threshold(blur, THRESHOLD, 255, cv.THRESH_BINARY)

        # Außerhalb der Maske entstandene Artefakte aus Otsu entfernen
        thresh = cv.bitwise_and(thresh, self._trapez_mask)
        cv.imwrite(os.path.join(self._base_images_dir, "bin", f"image_{self._test_counter}.png"), thresh)

        contours, _ = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        contours = [cnt for cnt in contours if cv.contourArea(cnt) >= MIN_CONTOUR_AREA]
        contours = sorted(
            contours,
            key=lambda cnt: cv.moments(cnt)["m10"] / cv.moments(cnt)["m00"],
            reverse=True
        )

        if not contours:
            raise ValueError("Keine Konturen im ROI gefunden.")

        objects = []

        for cnt in contours:
            M = cv.moments(cnt)
            if M["m00"] != 0:
                cx_roi = float(M["m10"] / M["m00"])
                cy_roi = float(M["m01"] / M["m00"])
            else:
                cx_roi, cy_roi = 0.0, 0.0

            cx_px = cx_roi + self._rx
            cy_px = cy_roi + self._ry

            X_w, Y_w = self.pixel_zu_welt(cx_px, cy_px)
            X_w_m, Y_w_m, Z_w_m = self.convert(X_w, Y_w, Z_W_CONSTANT_IN_MM)

            if not self._plausi.check_position([X_w_m, Y_w_m, Z_w_m]):
                raise ValueError(f"Unplausible Koordinaten: ({X_w_m:.2f}, {Y_w_m:.2f}, {Z_w_m:.2f})")
            

            objects.append((X_w_m, Y_w_m, Z_w_m))
            print(f"[OcvP][getImageData]: Detected object at pixel world ({X_w_m:.1f}, {Y_w_m:.1f})")

        result = (objects, self.time_stamp_ms, thresh)
        self._last_result = result
        return result

    def getLastImageData(self):
        return self._last_result

    def release(self):
        if self._cap.isOpened():
            self._cap.release()