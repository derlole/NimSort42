import cv2 as cv
import time
import numpy as np
from nimsort_vision.opencv_pieline_interface import OpencvPipelineInterface

CAMERA_INDEX = 4
MIN_CONTOUR_AREA = 4500

ROI_POINTS = np.array([
    [10,  122],   # oben-links
    [630, 122],   # oben-rechts
    [630, 270],   # unten-rechts
    [10,  300],   # unten-links
], dtype=np.float32)

PIXEL_PUNKTE = np.array([
    [69, 62],   [113, 62],  [114, 109], [70, 109],
    [159, 61],  [202, 61],  [204, 107], [160, 108],
], dtype=np.float32)

WELT_PUNKTE = np.array([
    [56, 25],  [76, 25],  [76, 5],   [56, 5],
    [98, 25],  [118, 25], [118, 5],  [98, 5],
], dtype=np.float32)


class OpencvPipeline(OpencvPipelineInterface):

    def __init__(self):
        self.time_stamp_ms = None
        self._last_result = None
        self._cap = cv.VideoCapture(CAMERA_INDEX)
        if not self._cap.isOpened():
            raise RuntimeError(f"Kamera {CAMERA_INDEX} konnte nicht geöffnet werden.")

        # Homographie berechnen
        self.H, _ = cv.findHomography(PIXEL_PUNKTE, WELT_PUNKTE)

        # ROI-Bounding-Box vorberechnen (für schnellen Slice)
        pts = ROI_POINTS.astype(np.int32)
        self._rx  = int(pts[:, 0].min())   # x-Start
        self._ry  = int(pts[:, 1].min())   # y-Start
        rx2       = int(pts[:, 0].max())   # x-Ende
        ry2       = int(pts[:, 1].max())   # y-Ende
        self._roi_slice = (slice(self._ry, ry2), slice(self._rx, rx2))

        # Trapez-Maske relativ zur Bounding-Box vorberechnen
        pts_shifted = pts - np.array([self._rx, self._ry])
        mask_h = ry2 - self._ry
        mask_w = rx2 - self._rx
        self._roi_mask = np.zeros((mask_h, mask_w), dtype=np.uint8)
        cv.fillPoly(self._roi_mask, [pts_shifted], 255)

    def pixel_zu_welt(self, u, v):
        p = np.array([u, v, 1.0])
        w = self.H @ p
        w /= w[2]
        return round(w[0], 1), round(w[1], 1)

    def captureImage(self):
        """Liest exklusiv den Rohframe – minimale Laufzeit."""
        ret, self._raw_image = self._cap.read()
        self.time_stamp_ms = int(time.time() * 1000)
        if not ret or self._raw_image is None:
            raise RuntimeError("Bildaufnahme fehlgeschlagen.")

    def getImageData(self):
        if self._raw_image is None:
            raise RuntimeError("Kein Bild – zuerst captureImage() aufrufen.")

        # 1. Bounding-Box-Slice → schneller Speicherzugriff
        roi = self._raw_image[self._roi_slice]

        # 2. Trapez-Maske anwenden → Pixel außerhalb = 0
        roi_masked = cv.bitwise_and(roi, roi, mask=self._roi_mask)

        # 3. Verarbeitung nur auf dem maskierten ROI
        gray = cv.cvtColor(roi_masked, cv.COLOR_BGR2GRAY)
        blur = cv.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv.threshold(blur, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

        # Maske aus Schwellwert mit ROI-Maske UND-verknüpfen,
        # damit Trapez-Rand nicht als Kontur erkannt wird
        thresh = cv.bitwise_and(thresh, self._roi_mask)

        contours, _ = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        contours = [cnt for cnt in contours if cv.contourArea(cnt) >= MIN_CONTOUR_AREA]
        contours = sorted(
            contours,
            key=lambda cnt: cv.moments(cnt)["m10"] / cv.moments(cnt)["m00"],
            reverse=True
        )

        if not contours:
            raise RuntimeError("Keine Konturen im ROI gefunden.")

        contour = contours[0]
        M = cv.moments(contour)
        if M["m00"] != 0:
            cx_roi = float(M["m10"] / M["m00"])
            cy_roi = float(M["m01"] / M["m00"])
        else:
            cx_roi, cy_roi = 0.0, 0.0

        # Schwerpunkt zurück in Vollbild-Koordinaten
        cx_px = cx_roi + self._rx
        cy_px = cy_roi + self._ry

        X_c, Y_c = self.pixel_zu_welt(cx_px, cy_px)
        Z_c = 0.0

        result = (X_c, Y_c, Z_c, self.time_stamp_ms, roi_masked)
        self._last_result = result
        return result

    def getLastImageData(self):
        return self._last_result

    def release(self):
        if self._cap.isOpened():
            self._cap.release()