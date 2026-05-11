import cv2 as cv
import numpy as np
import time

from nimsort_vision.opencv_pieline_interface import OpencvPipelineInterface

class OpencvPipelineAruco(OpencvPipelineInterface):
    def __init__(self):
        self.camera_index = 4
        self.image = None
        self.timestamp = None
        self._last_result = None

        self.camera_matrix = np.array([
            [2470.6158742234998, 0.0, 536.6431517087357],
            [0.0, 2449.454166610392, 234.50734304897156],
            [0.0, 0.0, 1.0]
        ], dtype=np.float64)

        self.dist_coeff = np.array([
            -0.2139440134403675, -24.358573379001676, 0.006326811273390342,
            -0.03215022298226852, 289.2947414539591
        ], dtype=np.float64)

        self.aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_4X4_50)
        self.parameters = cv.aruco.DetectorParameters()
        self.marker_length = 0.1  # Marker size in meters
        self.detector = cv.aruco.ArucoDetector(self.aruco_dict, self.parameters)

        self._new_camera_matrix = None
        self._roi = None
        self._image_shape = None

    def _init_undistort_maps(self, image_shape):
        h, w = image_shape[:2]
        new_camera_matrix, roi = cv.getOptimalNewCameraMatrix(
            self.camera_matrix, self.dist_coeff, (w, h), alpha=1, newImgSize=(w, h)
        )
        self._new_camera_matrix = new_camera_matrix
        self._roi = roi
        self._image_shape = image_shape[:2]

    def _undistort(self, image):
        if self._image_shape != image.shape[:2]:
            self._init_undistort_maps(image.shape)
        return cv.undistort(image, self.camera_matrix, self.dist_coeff, None, self._new_camera_matrix)

    def _pixel_to_camera(self, cx_px, cy_px, marker_rvec, marker_tvec):
        K = self._new_camera_matrix if self._new_camera_matrix is not None else self.camera_matrix
        uv = np.array([cx_px, cy_px, 1.0])
        uv_norm = np.linalg.inv(K) @ uv
        X_norm, Y_norm = uv_norm[0] / uv_norm[2], uv_norm[1] / uv_norm[2]

        # Assume object is at same Z as marker (plane assumption)
        Z_c = marker_tvec[2][0]  # Marker distance as approximation
        X_c = X_norm * Z_c
        Y_c = Y_norm * Z_c

        return float(X_c), float(Y_c), float(Z_c)

    def captureImage(self):
        cap = cv.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError(f"Camera {self.camera_index} not opened.")

        cap.set(cv.CAP_PROP_BUFFERSIZE, 1)
        ret, frame = cap.read()
        self.timestamp = int(time.time() * 1000)
        cap.release()

        if not ret or frame is None:
            raise RuntimeError("Image capture failed.")

        self.image = frame

    def getImageData(self):
        if self.image is None:
            raise RuntimeError("No image captured.")

        undistorted = self._undistort(self.image)
        image = undistorted.copy()

        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        corners, ids, rejected = self.detector.detectMarkers(gray)

        if ids is None or len(ids) == 0:
            raise RuntimeError("No ArUco marker detected.")

        # Use first marker
        marker_corners = corners[0]
        rvec, tvec, _ = cv.aruco.estimatePoseSingleMarkers(
            marker_corners, self.marker_length, self.camera_matrix, self.dist_coeff
        )

        # Draw marker
        cv.aruco.drawDetectedMarkers(image, corners, ids)
        cv.drawFrameAxes(image, self.camera_matrix, self.dist_coeff, rvec[0], tvec[0], 0.05)

        # Process objects (assume largest contour near marker)
        blur = cv.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv.threshold(blur, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
        contours, _ = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        contours = [cnt for cnt in contours if cv.contourArea(cnt) >= 50]
        contours = sorted(contours, key=cv.contourArea, reverse=True)

        if not contours:
            raise RuntimeError("No contours found.")

        contour = contours[0]
        M = cv.moments(contour)
        cx_px = float(M["m10"] / M["m00"]) if M["m00"] != 0 else 0.0
        cy_px = float(M["m01"] / M["m00"]) if M["m00"] != 0 else 0.0

        X_c, Y_c, Z_c = self._pixel_to_camera(cx_px, cy_px, rvec[0], tvec[0])

        cv.drawContours(image, [contour], -1, (0, 255, 0), 2)
        cv.circle(image, (int(cx_px), int(cy_px)), 5, (0, 0, 255), -1)
        cv.putText(image, f"cam: ({X_c:.4f}, {Y_c:.4f}, {Z_c:.4f})", (int(cx_px) + 10, int(cy_px) - 10),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

        result = (X_c, Y_c, Z_c, self.timestamp, image)
        self._last_result = result
        return result

    def getLastImageData(self):
        return self._last_result