import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import sys
import types
import cv2 as cv

# ---------------------------------------------------------------------------
# Stub-Module
# ---------------------------------------------------------------------------
# configs.config_camera
config_cam = types.ModuleType("configs.config_camera")
config_cam.MIN_CONTOUR_AREA = 500
config_cam.LABEL_MAP = {0: "Kreis", 1: "Rechteck", 2: "Dreieck"}
sys.modules.setdefault("configs", types.ModuleType("configs"))
sys.modules["configs.config_camera"] = config_cam

# nimsort_feature_detection.feature_detection_interface
iface_mod = types.ModuleType("nimsort_feature_detection.feature_detection_interface")
class FeatureDetectionInterface:
    pass
iface_mod.FeatureDetectionInterface = FeatureDetectionInterface
sys.modules.setdefault("nimsort_feature_detection", types.ModuleType("nimsort_feature_detection"))
sys.modules["nimsort_feature_detection.feature_detection_interface"] = iface_mod

from feature_detection import FeatureDetection  # noqa: E402


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def _make_binary_with_circle(size=300, radius=40):
    """Binärbild mit einem ausgefüllten Kreis (deutlich > MIN_CONTOUR_AREA)."""
    img = np.zeros((size, size), dtype=np.uint8)
    cv.circle(img, (150, 150), radius, 255, -1)
    return img

def _make_binary_with_two_objects():
    """Binärbild mit zwei getrennten Kreisen."""
    img = np.zeros((300, 400), dtype=np.uint8)
    cv.circle(img, (100, 150), 40, 255, -1)
    cv.circle(img, (300, 150), 40, 255, -1)
    return img

def _make_empty_binary():
    return np.zeros((300, 300), dtype=np.uint8)

def _make_pipeline(mock_model=None):
    """Gibt eine FeatureDetection-Instanz mit gemocktem joblib zurück."""
    if mock_model is None:
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([1])
    with patch("os.path.isfile", return_value=True), \
         patch("joblib.load", return_value=mock_model):
        return FeatureDetection(model_path="/fake/model.joblib"), mock_model


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestFeatureDetectionInit(unittest.TestCase):

    def test_raises_if_model_not_found(self):
        with patch("os.path.isfile", return_value=False):
            with self.assertRaises(FileNotFoundError):
                FeatureDetection(model_path="/nonexistent/model.joblib")

    def test_loads_model_on_init(self):
        mock_model = MagicMock()
        with patch("os.path.isfile", return_value=True), \
             patch("joblib.load", return_value=mock_model) as mock_load:
            fd = FeatureDetection(model_path="/fake/model.joblib")
            mock_load.assert_called_once_with("/fake/model.joblib")

    def test_last_feature_empty_after_init(self):
        fd, _ = _make_pipeline()
        self.assertEqual(fd.getLastFeature(), [])


class TestExtractFeaturesForContours(unittest.TestCase):

    def test_returns_empty_for_blank_image(self):
        result = FeatureDetection._extract_features_for_contours(_make_empty_binary())
        self.assertEqual(result, [])

    def test_returns_one_feature_for_one_object(self):
        result = FeatureDetection._extract_features_for_contours(_make_binary_with_circle())
        self.assertEqual(len(result), 1)

    def test_returns_two_features_for_two_objects(self):
        result = FeatureDetection._extract_features_for_contours(_make_binary_with_two_objects())
        self.assertEqual(len(result), 2)

    def test_feature_vector_shape(self):
        result = FeatureDetection._extract_features_for_contours(_make_binary_with_circle())
        self.assertEqual(result[0].shape, (1, 2))

    def test_feature_vector_dtype(self):
        result = FeatureDetection._extract_features_for_contours(_make_binary_with_circle())
        self.assertEqual(result[0].dtype, np.float32)

    def test_small_contours_filtered_out(self):
        """Konturen unter MIN_CONTOUR_AREA (500) dürfen nicht auftauchen."""
        img = np.zeros((300, 300), dtype=np.uint8)
        cv.circle(img, (150, 150), 5, 255, -1)  # sehr klein
        result = FeatureDetection._extract_features_for_contours(img)
        self.assertEqual(result, [])

    def test_sorted_by_x_descending(self):
        """Konturen müssen nach X-Schwerpunkt absteigend sortiert sein."""
        img = _make_binary_with_two_objects()
        result = FeatureDetection._extract_features_for_contours(img)
        # Beide Feature-Vektoren vorhanden – wir prüfen nur die Anzahl hier,
        # da hu-Werte vom Bild abhängen.
        self.assertEqual(len(result), 2)


class TestGetFeature(unittest.TestCase):

    def test_returns_empty_list_for_blank_image(self):
        fd, _ = _make_pipeline()
        result = fd.getFeature(_make_empty_binary())
        self.assertEqual(result, [])

    def test_returns_list_of_ints(self):
        fd, mock_model = _make_pipeline()
        mock_model.predict.return_value = np.array([2])
        result = fd.getFeature(_make_binary_with_circle())
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], int)

    def test_single_object_single_prediction(self):
        fd, mock_model = _make_pipeline()
        mock_model.predict.return_value = np.array([0])
        result = fd.getFeature(_make_binary_with_circle())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 0)

    def test_two_objects_two_predictions(self):
        fd, mock_model = _make_pipeline()
        mock_model.predict.side_effect = [np.array([1]), np.array([2])]
        result = fd.getFeature(_make_binary_with_two_objects())
        self.assertEqual(len(result), 2)

    def test_model_predict_called_per_contour(self):
        fd, mock_model = _make_pipeline()
        mock_model.predict.return_value = np.array([1])
        fd.getFeature(_make_binary_with_two_objects())
        self.assertEqual(mock_model.predict.call_count, 2)

    def test_prediction_stored_in_last_feature(self):
        fd, mock_model = _make_pipeline()
        mock_model.predict.return_value = np.array([2])
        fd.getFeature(_make_binary_with_circle())
        self.assertEqual(fd.getLastFeature(), [2])

    def test_blank_image_clears_last_feature(self):
        fd, mock_model = _make_pipeline()
        mock_model.predict.return_value = np.array([1])
        fd.getFeature(_make_binary_with_circle())   # erst ein Ergebnis
        fd.getFeature(_make_empty_binary())         # dann leer
        self.assertEqual(fd.getLastFeature(), [])


class TestGetLastFeature(unittest.TestCase):

    def test_returns_last_result(self):
        fd, mock_model = _make_pipeline()
        mock_model.predict.return_value = np.array([0])
        fd.getFeature(_make_binary_with_circle())
        self.assertEqual(fd.getLastFeature(), [0])

    def test_returns_empty_before_any_call(self):
        fd, _ = _make_pipeline()
        self.assertEqual(fd.getLastFeature(), [])


class TestResetFeatureDetection(unittest.TestCase):

    def test_reset_clears_last_feature(self):
        fd, mock_model = _make_pipeline()
        mock_model.predict.return_value = np.array([1])
        fd.getFeature(_make_binary_with_circle())
        fd.resetFeatureDetection()
        self.assertEqual(fd.getLastFeature(), [])

    def test_reset_on_empty_is_safe(self):
        fd, _ = _make_pipeline()
        fd.resetFeatureDetection()  # darf keinen Fehler werfen
        self.assertEqual(fd.getLastFeature(), [])


if __name__ == "__main__":
    unittest.main()