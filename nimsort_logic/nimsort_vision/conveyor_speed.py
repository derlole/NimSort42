

class ConveyorSpeedEstimator:
    """
    Schätzt die Förderbandgeschwindigkeit anhand von zwei aufeinanderfolgenden
    Objektpositionen (gleiche Objekte, erkannt in zwei Frames).
    """
    def __init__(self, smoothing: float = 0.3):
        self._last_x: float | None = None
        self._last_ts_ms: int | None = None
        self._estimated_speed: float = 0.0
        self._alpha = smoothing  # EMA-Glättungsfaktor (0 = träge, 1 = reaktiv)

    def update(self, x_m: float, ts_ms: int) -> float | None:
        """
        Gibt die geschätzte Geschwindigkeit in m/s zurück,
        oder None wenn noch kein vorheriger Messwert vorliegt.
        """
        if self._last_x is None or self._last_ts_ms is None:
            self._last_x = x_m
            self._last_ts_ms = ts_ms
            return None

        delta_x_m = x_m - self._last_x
        delta_t_s = (ts_ms - self._last_ts_ms) / 1000.0

        if delta_t_s <= 0:
            return None

        raw_speed = delta_x_m / delta_t_s

        # Exponential Moving Average zur Glättung
        self._estimated_speed = (
            self._alpha * raw_speed + (1 - self._alpha) * self._estimated_speed
        )

        self._last_x = x_m
        self._last_ts_ms = ts_ms

        return self._estimated_speed

    def reset(self):
        self._last_x = None
        self._last_ts_ms = None