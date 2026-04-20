"""
figure_tuner.py
---------------
Interaktives Tuning-Tool für figure_detector.py.
Alle relevanten Parameter sind per Trackbar live einstellbar.
ROI per Maus ziehen — nur dieser Bereich wird analysiert.

Zwei Fenster:
  "Tuning"  → Trackbars + Originalbild mit Konturen + ROI
  "Maske"   → Binärmaske live

Am Ende: [s] drücken → Werte erscheinen in der Konsole zum Kopieren.

Steuerung:
  Maus ziehen  → ROI definieren
  [r]          → ROI zurücksetzen
  [s]          → aktuelle Parameterwerte in Konsole ausgeben
  [q/ESC]      → Beenden
"""

import cv2
import numpy as np

CAMERA_INDEX  = 0
DISPLAY_SCALE = 0.85

WIN_TUNING = "Tuning  |  Maus=ROI  [r]=reset  [s]=Werte  [q]=Beenden"
WIN_MASK   = "Maske (Binaerbild)"


# ─────────────────────────────────────────────────────────────────────────────
# ROI-Zustand
# ─────────────────────────────────────────────────────────────────────────────

class ROIState:
    def __init__(self):
        self.x1 = self.y1 = self.x2 = self.y2 = 0
        self.drawing = False
        self.defined = False

    def as_rect(self):
        x = min(self.x1, self.x2)
        y = min(self.y1, self.y2)
        w = abs(self.x2 - self.x1)
        h = abs(self.y2 - self.y1)
        return x, y, w, h

    def valid(self):
        x, y, w, h = self.as_rect()
        return self.defined and w > 10 and h > 10


roi_state = ROIState()


def mouse_callback(event, x, y, flags, param):
    scale = param if param else 1.0
    ox = int(x / scale)
    oy = int(y / scale)

    if event == cv2.EVENT_LBUTTONDOWN:
        roi_state.drawing = True
        roi_state.x1 = roi_state.x2 = ox
        roi_state.y1 = roi_state.y2 = oy
        roi_state.defined = False
    elif event == cv2.EVENT_MOUSEMOVE and roi_state.drawing:
        roi_state.x2 = ox
        roi_state.y2 = oy
    elif event == cv2.EVENT_LBUTTONUP:
        roi_state.x2 = ox
        roi_state.y2 = oy
        roi_state.drawing = False
        roi_state.defined = True

def nothing(_):
    pass


def create_trackbars():
    cv2.namedWindow(WIN_TUNING, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN_TUNING, 900, 620)
    cv2.namedWindow(WIN_MASK, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN_MASK, 640, 480)

    cv2.setMouseCallback(WIN_TUNING, mouse_callback, DISPLAY_SCALE)

    # HSV Hintergrund
    cv2.createTrackbar("BG H Min",    WIN_TUNING,  90, 179, nothing)
    cv2.createTrackbar("BG H Max",    WIN_TUNING, 130, 179, nothing)
    cv2.createTrackbar("BG S Min",    WIN_TUNING,  40, 255, nothing)
    cv2.createTrackbar("BG V Min",    WIN_TUNING,  80, 255, nothing)
    # Weiß
    cv2.createTrackbar("W S Max",     WIN_TUNING,  40, 255, nothing)
    cv2.createTrackbar("W V Min",     WIN_TUNING, 200, 255, nothing)
    # Blur
    cv2.createTrackbar("Blur (x2+1)", WIN_TUNING,   2,  10, nothing)
    # Morphologie
    cv2.createTrackbar("Close Iter",  WIN_TUNING,   3,  10, nothing)
    cv2.createTrackbar("Open Iter",   WIN_TUNING,   1,   5, nothing)
    # Kontur
    cv2.createTrackbar("Min Area",    WIN_TUNING, 500, 5000, nothing)


def read_trackbars() -> dict:
    return {
        "bg_h_min":    cv2.getTrackbarPos("BG H Min",    WIN_TUNING),
        "bg_h_max":    cv2.getTrackbarPos("BG H Max",    WIN_TUNING),
        "bg_s_min":    cv2.getTrackbarPos("BG S Min",    WIN_TUNING),
        "bg_v_min":    cv2.getTrackbarPos("BG V Min",    WIN_TUNING),
        "white_s_max": cv2.getTrackbarPos("W S Max",     WIN_TUNING),
        "white_v_min": cv2.getTrackbarPos("W V Min",     WIN_TUNING),
        "blur_k":      cv2.getTrackbarPos("Blur (x2+1)", WIN_TUNING) * 2 + 1,
        "close_iter":  max(1, cv2.getTrackbarPos("Close Iter", WIN_TUNING)),
        "open_iter":   max(1, cv2.getTrackbarPos("Open Iter",  WIN_TUNING)),
        "min_area":    max(1, cv2.getTrackbarPos("Min Area",   WIN_TUNING)),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Bildverarbeitung
# ─────────────────────────────────────────────────────────────────────────────

def apply_roi(frame: np.ndarray) -> np.ndarray:
    if not roi_state.valid():
        return frame.copy()
    x, y, w, h = roi_state.as_rect()
    masked = np.zeros_like(frame)
    masked[y:y+h, x:x+w] = frame[y:y+h, x:x+w]
    return masked


def preprocess(frame: np.ndarray, p: dict) -> np.ndarray:
    roi_frame = apply_roi(frame)

    k = p["blur_k"] if p["blur_k"] % 2 == 1 else p["blur_k"] + 1
    blurred = cv2.GaussianBlur(roi_frame, (k, k), 0)

    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    H, S, V = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

    bg_mask = (
        (H >= p["bg_h_min"]) & (H <= p["bg_h_max"]) &
        (S >= p["bg_s_min"]) &
        (V >= p["bg_v_min"])
    ).astype(np.uint8) * 255

    gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
    white_mask = ((S <= p["white_s_max"]) & (V >= p["white_v_min"])).astype(np.uint8) * 255
    _, bright_mask = cv2.threshold(gray, p["white_v_min"], 255, cv2.THRESH_BINARY)
    white_mask = cv2.bitwise_and(white_mask, bright_mask)

    combined = cv2.bitwise_and(white_mask, cv2.bitwise_not(bg_mask))

    kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    kernel_tiny  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))

    closed = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel_small, iterations=p["close_iter"])

    # Flood Fill — Löcher im Inneren schließen
    filled = closed.copy()
    h_f, w_f = filled.shape
    flood_mask = np.zeros((h_f + 2, w_f + 2), dtype=np.uint8)
    cv2.floodFill(filled, flood_mask, (0, 0), 255)
    filled_inv  = cv2.bitwise_not(filled)
    closed_fill = cv2.bitwise_or(closed, filled_inv)

    opened = cv2.morphologyEx(closed_fill, cv2.MORPH_OPEN, kernel_tiny, iterations=p["open_iter"])
    return opened


# ─────────────────────────────────────────────────────────────────────────────
# Visualisierung
# ─────────────────────────────────────────────────────────────────────────────

def draw(frame: np.ndarray, mask: np.ndarray, min_area: int) -> np.ndarray:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours    = [c for c in contours if cv2.contourArea(c) >= min_area]

    vis = frame.copy()

    # ROI einzeichnen
    if roi_state.valid():
        x, y, w, h = roi_state.as_rect()
        cv2.rectangle(vis, (x, y), (x+w, y+h), (0, 180, 255), 2)
        cv2.putText(vis, "ROI", (x+4, y+18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 180, 255), 1)
    elif roi_state.drawing:
        cv2.rectangle(vis,
                      (roi_state.x1, roi_state.y1),
                      (roi_state.x2, roi_state.y2),
                      (0, 120, 255), 1)

    # Konturen
    cv2.drawContours(vis, contours, -1, (0, 255, 80), 2)
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(vis, (x, y), (x+w, y+h), (255, 180, 0), 1)
        cv2.putText(vis, f"A={cv2.contourArea(c):.0f}", (x, max(y-4, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

    roi_hint = "ROI aktiv  [r]=reset" if roi_state.valid() else "Maus ziehen = ROI  [r]=reset"
    cv2.putText(vis, f"Figuren: {len(contours)}  |  {roi_hint}",
                (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    return vis


# ─────────────────────────────────────────────────────────────────────────────
# Parameter-Ausgabe
# ─────────────────────────────────────────────────────────────────────────────

def print_params(p: dict):
    print("\n" + "=" * 55)
    print("  Optimierte Parameter — in figure_detector.py eintragen:")
    print("=" * 55)
    print(f"  WHITE_THRESHOLD      = {p['white_v_min']}")
    print(f"  BLUE_H_MIN           = {p['bg_h_min']}")
    print(f"  BLUE_H_MAX           = {p['bg_h_max']}")
    print(f"  BLUE_S_MIN           = {p['bg_s_min']}")
    print(f"  BLUE_V_MIN           = {p['bg_v_min']}")
    print(f"  WHITE_S_MAX          = {p['white_s_max']}")
    print(f"  Blur Kernel          = ({p['blur_k']}, {p['blur_k']})")
    print(f"  Close iterations     = {p['close_iter']}")
    print(f"  Open  iterations     = {p['open_iter']}")
    print(f"  MIN_CONTOUR_AREA     = {p['min_area']}")
    if roi_state.valid():
        x, y, w, h = roi_state.as_rect()
        print(f"\n  ROI (x, y, w, h)     = ({x}, {y}, {w}, {h})")
    print("=" * 55 + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Hauptschleife
# ─────────────────────────────────────────────────────────────────────────────

def main():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        raise RuntimeError(f"Kamera {CAMERA_INDEX} konnte nicht geöffnet werden.")

    create_trackbars()
    print("Tuner gestartet.")
    print("  → Maus ziehen = ROI   [r] = ROI reset")
    print("  → [s] = Werte ausgeben   [q/ESC] = Beenden")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Kein Bild.")
            break

        p    = read_trackbars()
        mask = preprocess(frame, p)
        vis  = draw(frame, mask, p["min_area"])

        vis_small  = cv2.resize(vis,  None, fx=DISPLAY_SCALE, fy=DISPLAY_SCALE)
        mask_small = cv2.resize(
            cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR),
            None, fx=DISPLAY_SCALE, fy=DISPLAY_SCALE
        )

        cv2.imshow(WIN_TUNING, vis_small)
        cv2.imshow(WIN_MASK,   mask_small)

        raw_key = cv2.waitKey(30)
        key     = raw_key & 0xFF if raw_key != -1 else 0xFF

        if key == ord("q") or key == 27:
            break
        elif key == ord("r"):
            roi_state.defined = False
            roi_state.drawing = False
            print("[ROI] zurückgesetzt.")
        elif key == ord("s"):
            print_params(p)

    cap.release()
    cv2.destroyAllWindows()
    print("Beendet.")


if __name__ == "__main__":
    main()