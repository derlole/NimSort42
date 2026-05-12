import cv2 as cv
import numpy as np
import joblib
import os

from nimsort_vision.feature_detection_interface import FeatureDetectionInterface

# Klassen-Mapping – Index entspricht dem Rückgabewert
# 0 = einhorn | 1 = katze | 2 = kreis | 3 = quadrat
LABEL_MAP = {0: "einhorn", 1: "katze", 2: "kreis", 3: "quadrat"}
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "object_classifier.joblib")
MIN_CONTOUR_AREA = 4500


class FeatureDetection(FeatureDetectionInterface):
    """
    Klassifiziert Objekte im Binärbild anhand von hu_0 + fourier_2
    mit einem vortrainierten Decision-Tree-Modell (max_depth=5).

    Rückgabewert von getFeature():
        0 = einhorn  |  1 = katze  |  2 = kreis  |  3 = quadrat  |  -1 = Fehler
    """

    def __init__(self, model_path: str = _MODEL_PATH):
        if not os.path.isfile(model_path):
            raise FileNotFoundError(
                f"[FD][__init__]: Modell nicht gefunden: {model_path}\n"
                "Bitte zuerst train_classifier.py ausführen."
            )
        self._model = joblib.load(model_path)
        self._last_feature: int = -1
        print(f"[FD][__init__]: Modell geladen von '{model_path}'")

    # ------------------------------------------------------------------
    # Merkmals-Extraktion
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_features(binary_image: np.ndarray):
        """
        Extrahiert hu_0 und fourier_2 aus der größten Kontur des Binärbildes.

        hu_0     – erster Hu-Moment (normiertes zweites Moment, rotationsinvariant)
        fourier_2 – dritter Fourier-Deskriptor der Kontur (Index 2)

        Returns:
            np.ndarray shape (1, 2) mit [hu_0, fourier_2] oder None bei Fehler.
        """
        contours, _ = cv.findContours(binary_image, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        contours = [cnt for cnt in contours if cv.contourArea(cnt) >= MIN_CONTOUR_AREA]

        if not contours:
            return None

        cnt = max(contours, key=cv.contourArea)

        # ── hu_0 ──────────────────────────────────────────────────────
        moments = cv.moments(cnt)
        if moments["m00"] == 0:
            return None
        hu_raw = cv.HuMoments(moments).flatten()
        # Log-Transformation (wie beim Training)
        with np.errstate(divide="ignore"):
            hu_log = -np.sign(hu_raw) * np.log10(np.abs(hu_raw) + 1e-10)
        hu_0 = hu_log[0]

        # ── fourier_2 ─────────────────────────────────────────────────
        # Konturpunkte als komplexe Zahlen
        pts = cnt[:, 0, :].astype(np.float32)
        z = pts[:, 0] + 1j * pts[:, 1]

        # DFT der Kontur
        Z = np.fft.fft(z)
        N = len(Z)

        # Amplituden normiert auf den ersten Deskriptor (Größeninvarianz)
        amplitudes = np.abs(Z) / (np.abs(Z[1]) + 1e-10)

        # Index 2 (dritter Koeffizient)
        fourier_2 = float(amplitudes[2]) if N > 2 else 0.0

        return np.array([[hu_0, fourier_2]], dtype=np.float32)

    # ------------------------------------------------------------------
    # Interface-Methoden
    # ------------------------------------------------------------------

    def getFeature(self, binary_image: np.ndarray) -> int:
        """
        Klassifiziert das Objekt im übergebenen Binärbild.

        Args:
            binary_image: 8-bit Binärbild (0/255) direkt aus der OpencvPipeline.

        Returns:
            int: 0=einhorn | 1=katze | 2=kreis | 3=quadrat | -1=Fehler
        """
        features = self._extract_features(binary_image)

        if features is None:
            print("[FD][getFeature]: Keine Kontur gefunden – gebe -1 zurück.")
            self._last_feature = -1
            return -1

        prediction: int = int(self._model.predict(features)[0])
        self._last_feature = prediction
        print(
            f"[FD][getFeature]: hu_0={features[0,0]:.4f}, fourier_2={features[0,1]:.4f}"
            f" → {prediction} ({LABEL_MAP.get(prediction, 'unbekannt')})"
        )
        return prediction

    def getLastFeature(self) -> int:
        """Gibt das zuletzt klassifizierte Ergebnis zurück."""
        return self._last_feature

    def resetFeatureDetection(self) -> None:
        """Setzt den internen Zustand zurück."""
        self._last_feature = -1