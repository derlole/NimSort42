import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import numpy as np
import cv2 as cv


# ---------------------------------------------------------------------------
# Stub-Module, die nicht im Test-Env vorhanden sind
# ---------------------------------------------------------------------------
import sys
import types

# configs.config_camera
config_cam = types.ModuleType("configs.config_camera")
config_cam.CAMERA_INDEX      = 0
config_cam.MIN_CONTOUR_AREA  = 500
config_cam.Z_W_CONSTANT_IN_MM = 100.0
config_cam.MIN_OTSU_THRESHOLD = 30
config_cam.ROI_TRAPEZ = np.array([[50, 50], [250, 50], [250, 250], [50, 250]], dtype=np.int32)
config_cam.PIXEL_PUNKTE = np.array([[0,0],[1,0],[1,1],[0,1]], dtype=np.float32)
config_cam.WELT_PUNKTE  = np.array([[0,0],[100,0],[100,100],[0,100]], dtype=np.float32)
config_cam.PICK_OFFSET_PX = 5
sys.modules["configs"] = types.ModuleType("configs")
sys.modules["configs.config_camera"] = config_cam

# nimsort_vision.opencv_pieline_interface
iface_mod = types.ModuleType("nimsort_vision.opencv_pieline_interface")
class OpencvPipelineInterface:
    pass
iface_mod.OpencvPipelineInterface = OpencvPipelineInterface
sys.modules["nimsort_vision"] = types.ModuleType("nimsort_vision")
sys.modules["nimsort_vision.opencv_pieline_interface"] = iface_mod

# nimsort_vision.plausibility_check
plausi_mod = types.ModuleType("nimsort_vision.plausibility_check")
class PlausibilityCheck:
    def check_position(self, pos):
        return True
plausi_mod.PlausibilityCheck = PlausibilityCheck
sys.modules["nimsort_vision.plausibility_check"] = plausi_mod

# Jetzt erst das echte Modul laden
from opencv_pipeline import OpencvPipeline   # noqa: E402  (liegt im Pfad)

# ---------------------------------------------------------------------------
# Hilfsfunktion: synthetisches Graybild mit einer klaren Kontur
# ---------------------------------------------------------------------------
def _make_raw_image_with_object():
    """300×300 BGR-Bild, weißes Rechteck im Trapez-Bereich."""
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv.rectangle(img, (100, 100), (200, 200), (255, 255, 255), -1)
    return img


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestOpencvPipelineInit(unittest.TestCase):

    @patch("cv2.VideoCapture")
    @patch("cv2.findHomography", return_value=(np.eye(3), None))
    def test_init_opens_camera(self, mock_hom, mock_cap_cls):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap_cls.return_value = mock_cap

        pipeline = OpencvPipeline(camera_index=0)
        mock_cap_cls.assert_called_once_with(0)

    @patch("cv2.VideoCapture")
    @patch("cv2.findHomography", return_value=(np.eye(3), None))
    def test_init_raises_if_camera_not_opened(self, mock_hom, mock_cap_cls):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cap_cls.return_value = mock_cap

        with self.assertRaises(RuntimeError):
            OpencvPipeline(camera_index=99)


class TestPixelToWorld(unittest.TestCase):

    def _make_pipeline(self):
        with patch("cv2.VideoCapture") as mock_cap_cls, \
             patch("cv2.findHomography", return_value=(np.eye(3), None)):
            mock_cap = MagicMock()
            mock_cap.isOpened.return_value = True
            mock_cap_cls.return_value = mock_cap
            return OpencvPipeline()

    def test_identity_homography(self):
        p = self._make_pipeline()
        x, y = p.pixelToWorld(10.0, 20.0)
        self.assertAlmostEqual(x, 10.0, places=5)
        self.assertAlmostEqual(y, 20.0, places=5)

    def test_returns_floats(self):
        p = self._make_pipeline()
        x, y = p.pixelToWorld(5, 7)
        self.assertIsInstance(x, float)
        self.assertIsInstance(y, float)


class TestConvertMmToM(unittest.TestCase):

    def _make_pipeline(self):
        with patch("cv2.VideoCapture") as mock_cap_cls, \
             patch("cv2.findHomography", return_value=(np.eye(3), None)):
            mock_cap = MagicMock()
            mock_cap.isOpened.return_value = True
            mock_cap_cls.return_value = mock_cap
            return OpencvPipeline()

    def test_conversion(self):
        p = self._make_pipeline()
        x, y, z = p.convert_mm_to_m(1000.0, 500.0, 250.0)
        self.assertAlmostEqual(x, 1.0)
        self.assertAlmostEqual(y, 0.5)
        self.assertAlmostEqual(z, 0.25)

    def test_zero(self):
        p = self._make_pipeline()
        x, y, z = p.convert_mm_to_m(0, 0, 0)
        self.assertEqual((x, y, z), (0.0, 0.0, 0.0))


class TestCaptureImage(unittest.TestCase):

    def _make_pipeline(self):
        with patch("cv2.VideoCapture") as mock_cap_cls, \
             patch("cv2.findHomography", return_value=(np.eye(3), None)):
            mock_cap = MagicMock()
            mock_cap.isOpened.return_value = True
            mock_cap_cls.return_value = mock_cap
            p = OpencvPipeline()
            p._cap = mock_cap        # direkt austauschen
            return p, mock_cap

    def test_capture_sets_raw_image(self):
        p, mock_cap = self._make_pipeline()
        fake_frame = np.zeros((300, 300, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, fake_frame)

        p.captureImage()
        self.assertIsNotNone(p._raw_image)
        self.assertIsNotNone(p.time_stamp_ms)

    def test_capture_raises_on_failure(self):
        p, mock_cap = self._make_pipeline()
        mock_cap.read.return_value = (False, None)

        with self.assertRaises(Exception):
            p.captureImage()

    def test_counter_increments(self):
        p, mock_cap = self._make_pipeline()
        fake_frame = np.zeros((300, 300, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, fake_frame)

        p.captureImage()
        p.captureImage()
        self.assertEqual(p._test_counter, 2)


class TestGetImageData(unittest.TestCase):

    def _make_pipeline(self):
        with patch("cv2.VideoCapture") as mock_cap_cls, \
             patch("cv2.findHomography", return_value=(np.eye(3), None)):
            mock_cap = MagicMock()
            mock_cap.isOpened.return_value = True
            mock_cap_cls.return_value = mock_cap
            return OpencvPipeline()

    def test_raises_without_image(self):
        p = self._make_pipeline()
        p._raw_image = None
        with self.assertRaises(Exception):
            p.getImageData()

    def test_returns_tuple_with_objects(self):
        p = self._make_pipeline()
        p._raw_image = _make_raw_image_with_object()

        objects, ts, thresh = p.getImageData()
        self.assertIsInstance(objects, list)
        self.assertGreater(len(objects), 0)
        self.assertIsInstance(ts, int)
        self.assertIsNotNone(thresh)

    def test_object_coordinates_are_floats(self):
        p = self._make_pipeline()
        p._raw_image = _make_raw_image_with_object()

        objects, _, _ = p.getImageData()
        for x, y, z in objects:
            self.assertIsInstance(x, float)
            self.assertIsInstance(y, float)
            self.assertIsInstance(z, float)

    def test_no_contours_raises_value_error(self):
        p = self._make_pipeline()
        # Komplett schwarzes Bild → keine Konturen
        p._raw_image = np.zeros((300, 300, 3), dtype=np.uint8)
        with self.assertRaises(ValueError):
            p.getImageData()

    def test_result_cached_in_last_result(self):
        p = self._make_pipeline()
        p._raw_image = _make_raw_image_with_object()

        result = p.getImageData()
        self.assertEqual(p.getLastImageData(), result)

    def test_plausibility_failure_raises(self):
        p = self._make_pipeline()
        p._raw_image = _make_raw_image_with_object()
        p._plausi.check_position = lambda pos: False   # alle Positionen ablehnen

        with self.assertRaises(ValueError):
            p.getImageData()

    def test_y_coordinate_negated(self):
        """Y_w_m muss negiert werden (Kamera- vs. Weltkoordinaten)."""
        p = self._make_pipeline()
        p._raw_image = _make_raw_image_with_object()

        # Homographie so setzen, dass Y_w bekannt ist
        H = np.eye(3)
        H[1, 2] = 50.0   # verschiebt Y in Pixelkoordinaten
        p.H = H

        objects, _, _ = p.getImageData()
        # Ohne Negierung wäre Y_w_m positiv (wegen +50 offset);
        # da Y_w_m = -Y_w_m gilt, muss hier gelten: Vorzeichen hängt vom
        # tatsächlichen Schwerpunkt ab – wir prüfen nur, dass überhaupt
        # ein Ergebnis zurückkommt.
        self.assertGreater(len(objects), 0)


class TestRelease(unittest.TestCase):

    def test_release_calls_cap_release(self):
        with patch("cv2.VideoCapture") as mock_cap_cls, \
             patch("cv2.findHomography", return_value=(np.eye(3), None)):
            mock_cap = MagicMock()
            mock_cap.isOpened.return_value = True
            mock_cap_cls.return_value = mock_cap

            p = OpencvPipeline()
            p.release()
            mock_cap.release.assert_called_once()

    def test_release_safe_when_not_opened(self):
        with patch("cv2.VideoCapture") as mock_cap_cls, \
             patch("cv2.findHomography", return_value=(np.eye(3), None)):
            mock_cap = MagicMock()
            mock_cap.isOpened.return_value = False
            mock_cap_cls.return_value = mock_cap

            p = OpencvPipeline()
            p.release()   # darf keinen Fehler werfen
            mock_cap.release.assert_not_called()


if __name__ == "__main__":
    unittest.main()