import cv2 as cv
import time
import numpy as np
import os

from nimsort_vision.opencv_pieline_interface import OpencvPipelineInterface
from nimsort_vision.plausibility_check import PlausibilityCheck

from configs.config_camera import CAMERA_INDEX, MIN_CONTOUR_AREA, Z_W_CONSTANT_IN_MM, MIN_OTSU_THRESHOLD, ROI_TRAPEZ, PIXEL_PUNKTE, WELT_PUNKTE, PICK_OFFSET_PX

class OpencvPipeline(OpencvPipelineInterface):

    def __init__(self, camera_index = CAMERA_INDEX):
        self.time_stamp_ms = None
        self._last_result = None
        self._test_counter = 0
        self._plausi = PlausibilityCheck()

        # Basisverzeichnis für Bilder relativ zum Skript-Verzeichnis
        self._base_images_dir = os.path.join(os.path.dirname(__file__), "..", "images_live")
        os.makedirs(os.path.join(self._base_images_dir, "raw"), exist_ok=True)
        os.makedirs(os.path.join(self._base_images_dir, "roi"), exist_ok=True)
        os.makedirs(os.path.join(self._base_images_dir, "bin"), exist_ok=True)

        self._cap = cv.VideoCapture(camera_index)
        if not self._cap.isOpened():
            raise RuntimeError(f"Kamera {camera_index} konnte nicht geöffnet werden.")

        print(f"[OcvP][__init__]: Kamera {camera_index} geöffnet, warte auf Stabilisierung...")

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

    def pixelToWorld(self, u, v):
        p = np.array([u, v, 1.0])
        w = self.H @ p
        w /= w[2]
        return w[0], w[1]
    
    def convert_mm_to_m(self, x_mm, y_mm, z_mm):
        x_m = x_mm / 1000.0
        y_m = y_mm / 1000.0
        z_m = z_mm / 1000.0
        return x_m, y_m, z_m

    def captureImage(self):
        """Liest exklusiv den Rohframe – minimale Laufzeit."""
        self._test_counter += 1
        ret, self._raw_image = self._cap.read()
        self.time_stamp_ms = int(time.time() * 1000)
        cv.imwrite(os.path.join(self._base_images_dir, "raw", f"image_{self._test_counter}.png"), self._raw_image) #TODO remove after testing

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
        roi_masked = cv.bitwise_and(roi, roi, mask = self._trapez_mask)
        cv.imwrite(os.path.join(self._base_images_dir, "roi", f"image_{self._test_counter}.png"), roi_masked) #TODO remove after testing

        gray = cv.cvtColor(roi_masked, cv.COLOR_BGR2GRAY)
        blur = cv.GaussianBlur(gray, (5, 5), 0)
        otsu_val, thresh = cv.threshold(blur, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

        if otsu_val < MIN_OTSU_THRESHOLD:
            thresh = np.zeros_like(blur)

        thresh = cv.bitwise_and(thresh, self._trapez_mask)
        cv.imwrite(os.path.join(self._base_images_dir, "bin", f"image_{self._test_counter}.png"), thresh) #TODO remove after testing

        contours, _ = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
        contours = [cnt for cnt in contours if cv.contourArea(cnt) >= MIN_CONTOUR_AREA]
        contours = sorted(contours, key=lambda cnt: cv.moments(cnt)["m10"] / cv.moments(cnt)["m00"], reverse=True)

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

        # --- Pickpunkt-Verschiebung ---
            S = np.array([cx_px, cy_px], dtype=np.float32)
            min_dist = float('inf')
            naechster_punkt = None
            for punkt in cnt:
                p = np.array([punkt[0][0] + self._rx, punkt[0][1] + self._ry], dtype=np.float32)
                dist = np.linalg.norm(S - p)
                if dist < min_dist:
                    min_dist = dist
                    naechster_punkt = p
            richtung = S - naechster_punkt
            richtung_norm = richtung / np.linalg.norm(richtung)
            pick = S + richtung_norm * PICK_OFFSET_PX
            cx_px, cy_px = float(pick[0]), float(pick[1])

            X_w, Y_w = self.pixelToWorld(cx_px, cy_px)
            X_w_m, Y_w_m, Z_w_m = self.convert_mm_to_m(X_w, Y_w, Z_W_CONSTANT_IN_MM)
            
            Y_w_m = -Y_w_m # Negieren, da Weltkoordinaten Y-Achse entgegengesetzt zu Pixelkoordinaten

            if not self._plausi.check_position([X_w_m, Y_w_m, Z_w_m]):
                raise ValueError(f"Unplausible Koordinaten: ({X_w_m:.2f}, {Y_w_m:.2f}, {Z_w_m:.2f})")
            

            objects.append((X_w_m, Y_w_m, Z_w_m))
            print(f"[OcvP][getImageData]: Detected object at pixel world ({X_w_m:.4f}, {Y_w_m:.4f})")

        result = (objects, self.time_stamp_ms, thresh)
        self._last_result = result
        return result

    def getLastImageData(self):
        return self._last_result

    def release(self):
        if self._cap.isOpened():
            self._cap.release()