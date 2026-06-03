import cv2 as cv
import numpy as np
import joblib
import os

from nimsort_feature_detection.feature_detection_interface import FeatureDetectionInterface

from configs.config_camera import MIN_CONTOUR_AREA, LABEL_MAP

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "object_classifier.joblib")

class FeatureDetection(FeatureDetectionInterface):
    """
    Klassifiziert ALLE Objekte im Binärbild anhand von hu_0 + hu_3.

    Rückgabewert von getFeature():
        List[int] → z.B. [0,2,3]
    """

    def __init__(self, model_path: str = _MODEL_PATH):
        
        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"[FD][__init__]: Modell nicht gefunden: {model_path}\n""Bitte zuerst train_classifier.py ausführen.")

        self._model = joblib.load(model_path)
        self._last_feature = []
        print(f"[FD][__init__]: Modell geladen von '{model_path}'")


    @staticmethod
    def _extract_features_for_contours(binary_image: np.ndarray):
        """
        Extrahiert Features für ALLE gültigen Konturen.

        Returns:
            List[(feature_vector, contour)]
        """
        contours, _ = cv.findContours(binary_image, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        contours = [cnt for cnt in contours if cv.contourArea(cnt) >= MIN_CONTOUR_AREA]
        contours = sorted(contours, key=lambda cnt: cv.moments(cnt)["m10"] / cv.moments(cnt)["m00"], reverse=True)

        results = []

        for cnt in contours:
            moments = cv.moments(cnt)
            if moments["m00"] == 0:
                continue

            # ── hu_0 + hu_3 ──────────────────────
            hu_raw = cv.HuMoments(moments).flatten()
            with np.errstate(divide="ignore"):
                hu_log = -np.sign(hu_raw) * np.log10(np.abs(hu_raw) + 1e-10)

            hu_0 = hu_log[0]
            hu_3 = hu_log[3]

            feature_vec = np.array([[hu_0, hu_3]], dtype=np.float32)
            results.append((feature_vec, cnt))

        return results


    def getFeature(self, binary_image: np.ndarray):
        """
        Klassifiziert ALLE Objekte im Binärbild.

        Args:
            binary_image: Binärbild (0/255)

        Returns:
            List[int]: z.B. [0,2,3]
        """
        extracted = self._extract_features_for_contours(binary_image)

        if not extracted:
            print("[FD][getFeature]: Keine Konturen gefunden.")
            self._last_feature = []
            return []

        features = []

        for feature_vec, cnt in extracted:
            prediction: int = int(self._model.predict(feature_vec)[0])
            features.append(prediction)
            print(f"[FD][getFeature]: Prediction {prediction}")

            print(
                f"[FD]: hu_0={feature_vec[0,0]:.4f}, "
                f"hu_3={feature_vec[0,1]:.4f} "
                f"→ {prediction} ({LABEL_MAP.get(prediction, 'unbekannt')})"
            )

        self._last_feature = features
        return features

    def getLastFeature(self):
        """Gibt die letzte Feature-Liste zurück."""
        return self._last_feature

    def resetFeatureDetection(self):
        """Reset."""
        self._last_feature = []