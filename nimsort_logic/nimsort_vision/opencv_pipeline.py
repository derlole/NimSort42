import cv2 as cv
import time
import numpy as np
from nimsort_vision.opencv_pieline_interface import OpencvPipelineInterface

# --- Konfiguration ---
CAMERA_INDEX = 4

CAMERA_MATRIX = np.array([
    [2710.666860974311,    0.0,             367.8525523358933],
    [   0.0,           2766.057464263328,   245.68063913559047],
    [   0.0,              0.0,               1.0],
], dtype=np.float64)

DIST_COEFFS = np.array(
    [-1.4668410355213393, -19.46254234953102,
     -0.0022364037989029096, -0.03440200232868026,
     450.2793784546618],
    dtype=np.float64,
)

ROI = (10, 113, 615, 194)  # (x, y, width, height)

MIN_CONTOUR_AREA = 4500


class OpencvPipeline(OpencvPipelineInterface):

    def __init__(self):
        self.time_stamp = None
        self._last_result = None
        
        self._cap = cv.VideoCapture(CAMERA_INDEX)
        if not self._cap.isOpened():
            raise RuntimeError(f"Kamera {CAMERA_INDEX} konnte nicht geöffnet werden.")

        # Einmalig einen Frame lesen, um die Auflösung zu ermitteln
        ret, test_image = self._cap.read()
        if not ret or test_image is None:
            raise RuntimeError("Kein Test-Frame von der Kamera erhalten.")

        h, w = test_image.shape[:2]

        # Neue Kameramatrix + Remap-Maps vorberechnen
        new_cam_matrix, _ = cv.getOptimalNewCameraMatrix(
            CAMERA_MATRIX, DIST_COEFFS, (w, h), alpha=1, newImgSize=(w, h)
        )
        self._map1, self._map2 = cv.initUndistortRectifyMap(
            CAMERA_MATRIX, DIST_COEFFS, None,
            new_cam_matrix, (w, h), cv.CV_16SC2
        )

        # ROI-Slice + Offset einmalig vorberechnen
        x, y, rw, rh = ROI
        self._rx = x
        self._ry = y
        self._roi_slice = (slice(y, y + rh), slice(x, x + rw))

        # Kameramatrix-Werte als Skalare cachen für _pixel_to_camera
        self._fx = float(CAMERA_MATRIX[0, 0])
        self._fy = float(CAMERA_MATRIX[1, 1])
        self._cx = float(CAMERA_MATRIX[0, 2])
        self._cy = float(CAMERA_MATRIX[1, 2])

        self._raw_frame: np.ndarray | None = None

    # ------------------------------------------------------------------
    # Hilfsmethode
    # ------------------------------------------------------------------

    def _pixel_to_camera(self, u: float, v: float, Z: float = 1.0):
        """Konvertiert Pixelkoordinaten in normierte Kamerakoordinaten."""
        X_c = (u - self._cx) / self._fx * Z
        Y_c = (v - self._cy) / self._fy * Z
        return X_c, Y_c, Z

    # ------------------------------------------------------------------
    # Interface-Methoden
    # ------------------------------------------------------------------

    def captureImage(self):
        """Liest exklusiv den Rohframe – minimale Laufzeit."""
        ret, self._raw_frame = self._cap.read()
        self.time_stamp = int(time.time() * 1000)

        print(f"[OcvP][captureImage]: Frame captured at {self.time_stamp} ms")

        if not ret or self._raw_frame is None:
            raise RuntimeError("Bildaufnahme fehlgeschlagen.")

    def getImageData(self):
        """
        Entzerrt das zuletzt aufgenommene Bild, schneidet den ROI aus
        und berechnet den Schwerpunkt der größten Kontur in Kamerakoordinaten.

        Returns:
            (X_c: float, Y_c: float, Z_c: float, timestamp: int, roi_image: np.ndarray)
        """
        print(f"[OcvP][getImageData]: Processing image")
        if self._raw_frame is None:
            raise RuntimeError("Kein Bild – zuerst captureImage() aufrufen.")

        # 1) Entzerrung – remap ist schneller als undistort(), da Maps vorberechnet sind
        undistorted = cv.remap(self._raw_frame, self._map1, self._map2, cv.INTER_LINEAR)

        # 2) ROI per vorberechneter Slices – Zero-Copy-View, kein Overhead
        roi = undistorted[self._roi_slice]

        # 3) Graustufen → Blur → Otsu-Threshold
        gray = cv.cvtColor(roi, cv.COLOR_BGR2GRAY)
        blur = cv.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv.threshold(blur, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

        # 4) Konturen finden und nach Mindestfläche filtern
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

        # 8) Schwerpunkt in Vollbild-Pixelkoordinaten umrechnen
        cx_px = cx_roi + self._rx
        cy_px = cy_roi + self._ry

        # 9) Kamerakoordinaten berechnen
        X_c, Y_c, Z_c = self._pixel_to_camera(cx_px, cy_px)

        result = (X_c, Y_c, Z_c, self.time_stamp, roi)
        self._last_result = result
        return result

    def getLastImageData(self):
        """Get the image data from the last captured image"""
        return self._last_result

    # ------------------------------------------------------------------
    # Ressourcen-Verwaltung
    # ------------------------------------------------------------------

    def release(self):
        if self._cap.isOpened():
            self._cap.release()