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

        # Fester ROI (x, y, breite, höhe) – anpassen nach Bedarf!
        self.interest_roi = (30, 155, 600, 185)

        # Kalibrierungsdaten
        self.camera_matrix = np.array([
            [2470.6158742234998, 0.0,               536.6431517087357],
            [0.0,               2449.454166610392,  234.50734304897156],
            [0.0,               0.0,                1.0]
        ], dtype=np.float64)

        self.dist_coeff = np.array([
            -0.2139440134403675,
            -24.358573379001676,
            0.006326811273390342,
            -0.03215022298226852,
            289.2947414539591
        ], dtype=np.float64)

        # Optimierte Kameramatrix vorberechnen (wird bei erstem Bild gesetzt)
        self._new_camera_matrix = None
        self._roi = None
        self._image_shape = None

    def _init_undistort_maps(self, image_shape):
        """Berechnet Undistortion-Maps für die gegebene Bildgröße."""
        h, w = image_shape[:2]
        new_camera_matrix, roi = cv.getOptimalNewCameraMatrix(
            self.camera_matrix, self.dist_coeff, (w, h), alpha=1, newImgSize=(w, h)
        )
        self._new_camera_matrix = new_camera_matrix
        self._roi = roi
        self._image_shape = image_shape[:2]

    def _undistort(self, image):
        """Entzerrt das Bild mit den Kalibrierungsdaten."""
        if self._image_shape != image.shape[:2]:
            self._init_undistort_maps(image.shape)
        return cv.undistort(image, self.camera_matrix, self.dist_coeff, None, self._new_camera_matrix)

    def _pixel_to_camera(self, cx_px, cy_px):
        """
        Transformiert Pixelkoordinaten in normierte Kamerakoordinaten.

        Verwendet die (neue) Kameramatrix um den Schwerpunkt vom
        Bildkoordinatensystem ins Kamerakoordinatensystem zu überführen.
        Die Z-Komponente wird auf 1 normiert (keine Tiefeninformation).

            X_c = (u - cx) / fx
            Y_c = (v - cy) / fy
            Z_c = 1.0

        Args:
            cx_px (float): X-Pixelkoordinate
            cy_px (float): Y-Pixelkoordinate

        Returns:
            tuple: (X_c, Y_c, Z_c) normierte Kamerakoordinaten
        """
        K = self._new_camera_matrix if self._new_camera_matrix is not None else self.camera_matrix
        fx = K[0, 0]
        fy = K[1, 1]
        cx = K[0, 2]
        cy = K[1, 2]

        X_c = (cx_px - cx) / fx
        Y_c = (cy_px - cy) / fy
        Z_c = 1.0

        return float(X_c), float(Y_c), float(Z_c)

    def captureImage(self):
        """Capture the image from the camera"""
        cap = cv.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError(f"Kamera {self.camera_index} konnte nicht geöffnet werden.")

        cap.set(cv.CAP_PROP_BUFFERSIZE, 1)

        ret, frame = cap.read()
        self.timestamp = int(time.time() * 1000)
        cap.release()

        if not ret or frame is None:
            raise RuntimeError("Bild konnte nicht aufgenommen werden.")

        self.image = frame

    def getImageData(self):
        """Verarbeitet self.image und gibt den Schwerpunkt im Kamerakoordinatensystem zurück.

        Das Bild wird zunächst entzerrt (Undistortion), dann der Schwerpunkt
        der größten Kontur im definierten ROI berechnet und anschließend
        in Kamerakoordinaten umgerechnet.

        Returns:
            tuple: (X_c, Y_c, Z_c, timestamp, annotated_image)
                - X_c (float): X-Koordinate im Kamerakoordinatensystem (normiert)
                - Y_c (float): Y-Koordinate im Kamerakoordinatensystem (normiert)
                - Z_c (float): Z-Koordinate (immer 1.0, keine Tiefeninformation)
                - timestamp (int): Unix-Timestamp der Aufnahme in ms
                - annotated_image (np.ndarray): Entzerrtes Bild mit Konturen
        """
        if self.image is None:
            raise RuntimeError("Kein Bild vorhanden. Bitte zuerst captureImage() aufrufen.")

        # Bild entzerren
        undistorted = self._undistort(self.image)
        image = undistorted.copy()

        # ROI ausschneiden
        rx, ry, rw, rh = self.interest_roi
        roi = image[ry:ry+rh, rx:rx+rw]

        # Graustufen + Glätten + Threshold – nur auf dem ROI
        gray = cv.cvtColor(roi, cv.COLOR_BGR2GRAY)
        blur = cv.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv.threshold(blur, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

        # Konturen finden, filtern und sortieren
        contours, _ = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        contours = [cnt for cnt in contours if cv.contourArea(cnt) >= 50]
        contours = sorted(contours, key=cv.contourArea, reverse=True)

        if not contours:
            raise RuntimeError("Keine Konturen im ROI gefunden.")

        # Größte Kontur verwenden
        contour = contours[0]

        # Schwerpunkt in ROI-Koordinaten
        M = cv.moments(contour)
        if M["m00"] != 0:
            cx_roi = float(M["m10"] / M["m00"])
            cy_roi = float(M["m01"] / M["m00"])
        else:
            cx_roi, cy_roi = 0.0, 0.0

        # ROI-Koordinaten → Vollbild-Koordinaten
        cx_px = cx_roi + rx
        cy_px = cy_roi + ry

        # Schwerpunkt in Kamerakoordinaten umrechnen
        X_c, Y_c, Z_c = self._pixel_to_camera(cx_px, cy_px)

        # Annotierungen ins Vollbild zeichnen
        cv.rectangle(image, (rx, ry), (rx+rw, ry+rh), (0, 0, 255), 2)  # ROI-Rahmen
        cv.drawContours(roi, [contour], -1, (0, 255, 0), 2)              # Kontur im ROI
        cv.circle(image, (int(cx_px), int(cy_px)), 5, (0, 0, 255), -1)  # Schwerpunkt
        cv.putText(
            image,
            f"cam: ({X_c:.4f}, {Y_c:.4f})",
            (int(cx_px) + 10, int(cy_px) - 10),
            cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2
        )

        result = (X_c, Y_c, Z_c, self.timestamp, image)
        self._last_result = result
        return X_c, Y_c, Z_c, self.timestamp, image

    def getLastImageData(self) -> tuple[float, float, float, int, np.ndarray]:
        """Get the image data from the last captured image"""
        return self._last_result