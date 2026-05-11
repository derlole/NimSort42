"""
ArUco Marker Detektor – 3D XYZ Koordinaten
===========================================
Erkennt ArUco-Marker per Webcam und berechnet die 3D-Koordinaten (X, Y, Z)
der Eckpunkte im Kamerakoordinatensystem mithilfe der eingebetteten Kalibrierung.

Voreinstellung: Kamera 4, DICT_4X4_50, Marker-Seitenlänge 18.21 mm

Installation:
    pip install opencv-contrib-python numpy

Starten:
    python aruco_detector.py

Optionen:
    python aruco_detector.py --camera 4           # Kamera-Index (Standard: 4)
    python aruco_detector.py --dict DICT_4X4_50   # ArUco-Wörterbuch
    python aruco_detector.py --image bild.jpg     # Einzelbild statt Kamera

Koordinatensystem (Kamera-KS):
    X → rechts        (mm)
    Y → unten         (mm)
    Z → von Kamera weg (mm, = Abstand)

Eckpunkt-Reihenfolge (ArUco-Standard):
    E0 = oben links
    E1 = oben rechts
    E2 = unten rechts
    E3 = unten links
"""

import cv2
import numpy as np
import argparse
import sys
import time

# ── Kalibrierungsdaten ────────────────────────────────────────────────────────
CAMERA_MATRIX = np.array([
    [8551.027237070186,    0.0,             1097.9868366385667],
    [   0.0,           7842.141565217346,    377.63303851765414],
    [   0.0,              0.0,                1.0             ]
], dtype=np.float64)

DIST_COEFFS = np.array([
    -2.452975486976177,
     19.573130834430437,
      0.056176108223266616,
     -0.04577371058464672,
    821.4645129965147
], dtype=np.float64)

# Marker-Seitenlänge in mm (aus board_config → marker_length)
MARKER_LENGTH_MM = 18.214285714285715

# 3D-Eckpunkte im Marker-Koordinatensystem (Z=0-Ebene)
# Reihenfolge: oben-links, oben-rechts, unten-rechts, unten-links
HALF = MARKER_LENGTH_MM / 2.0
MARKER_OBJ_PTS = np.array([
    [-HALF,  HALF, 0.0],
    [ HALF,  HALF, 0.0],
    [ HALF, -HALF, 0.0],
    [-HALF, -HALF, 0.0],
], dtype=np.float64)

# ── Farben & Labels ───────────────────────────────────────────────────────────
CORNER_COLORS = [
    ( 60,  60, 220),   # E0 oben-links   → rot
    ( 50, 180,  50),   # E1 oben-rechts  → grün
    (220, 120,  40),   # E2 unten-rechts → blau
    ( 30, 160, 230),   # E3 unten-links  → orange
]
CORNER_LABELS = ["E0", "E1", "E2", "E3"]

ARUCO_DICTS = {
    "DICT_4X4_50":         cv2.aruco.DICT_4X4_50,
    "DICT_4X4_100":        cv2.aruco.DICT_4X4_100,
    "DICT_4X4_250":        cv2.aruco.DICT_4X4_250,
    "DICT_5X5_50":         cv2.aruco.DICT_5X5_50,
    "DICT_5X5_100":        cv2.aruco.DICT_5X5_100,
    "DICT_6X6_50":         cv2.aruco.DICT_6X6_50,
    "DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL,
}


# ── 3D-Berechnung ─────────────────────────────────────────────────────────────

def compute_3d_corners(image_corners_2d):
    """
    Berechnet XYZ der 4 Marker-Eckpunkte im Kamera-Koordinatensystem.

    Methode:
      1. solvePnP (IPPE_SQUARE) → Rotations-/Translationsvektor
      2. P_cam = R * P_marker + t  für jeden der 4 Eckpunkte

    Rückgabe:
      xyz  – (4,3) float64 in mm  oder None bei Fehler
      rvec – Rotationsvektor  (für Achsen-Visualisierung)
      tvec – Translationsvektor
    """
    pts2d = image_corners_2d.reshape((4, 2)).astype(np.float32)

    ok, rvec, tvec = cv2.solvePnP(
        MARKER_OBJ_PTS,
        pts2d,
        CAMERA_MATRIX,
        DIST_COEFFS,
        flags=cv2.SOLVEPNP_IPPE_SQUARE
    )
    if not ok:
        return None, None, None

    R, _ = cv2.Rodrigues(rvec)
    t    = tvec.flatten()

    xyz = np.array([R @ pt + t for pt in MARKER_OBJ_PTS])
    return xyz, rvec, tvec


# ── Zeichnen ──────────────────────────────────────────────────────────────────

def draw_axis(frame, rvec, tvec, length_mm=15.0):
    """Koordinatenkreuz am Marker-Mittelpunkt (X=rot, Y=grün, Z=blau)."""
    cv2.drawFrameAxes(frame, CAMERA_MATRIX, DIST_COEFFS,
                      rvec, tvec, length_mm, thickness=2)


def draw_marker(frame, corners_2d, marker_id, xyz):
    """
    Zeichnet Umriss, farbige Eckpunkte und 3D-Koordinaten ins Bild.
    xyz: (4,3)-Array in mm, oder None → nur Pixelkoordinaten
    """
    pts = corners_2d.reshape((4, 2)).astype(int)
    h, w = frame.shape[:2]

    # Marker-Umriss
    cv2.polylines(frame, [pts], isClosed=True,
                  color=(200, 160, 30), thickness=2, lineType=cv2.LINE_AA)

    # ID in der Mitte
    cx, cy = pts.mean(axis=0).astype(int)
    for color, thick in [((0, 0, 0), 3), ((255, 255, 255), 1)]:
        cv2.putText(frame, f"ID:{marker_id}",
                    (cx - 22, cy + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, thick, cv2.LINE_AA)

    # Eckpunkte
    for i, (px, py) in enumerate(pts):
        color = CORNER_COLORS[i]

        # Punkt
        cv2.circle(frame, (px, py), 7, color, -1, cv2.LINE_AA)
        cv2.circle(frame, (px, py), 7, (255, 255, 255), 1, cv2.LINE_AA)

        # Textzeilen aufbauen
        if xyz is not None:
            x3, y3, z3 = xyz[i]
            lines = [
                f"{CORNER_LABELS[i]}",
                f"X:{x3:+8.2f}mm",
                f"Y:{y3:+8.2f}mm",
                f"Z:{z3:+8.2f}mm",
            ]
        else:
            lines = [f"{CORNER_LABELS[i]} ({px},{py})"]

        # Position so wählen, dass Text im Bild bleibt
        tx = px + 10 if px < w - 150 else px - 155
        ty = py - 48 if py > 65    else py + 12

        for li, text in enumerate(lines):
            cv2.putText(frame, text, (tx, ty + li * 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.40,
                        (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(frame, text, (tx, ty + li * 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.40,
                        color, 1, cv2.LINE_AA)


def draw_hud(frame, num, dict_name, fps=None):
    """Info-Leiste oben links."""
    h = frame.shape[0]
    ov = frame.copy()
    cv2.rectangle(ov, (0, 0), (360, 80), (20, 20, 20), -1)
    cv2.addWeighted(ov, 0.55, frame, 0.45, 0, frame)

    cv2.putText(frame, f"ArUco 3D  [{dict_name}]",
                (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                (160, 160, 160), 1, cv2.LINE_AA)
    cv2.putText(frame,
                f"Marker: {num}   Laenge: {MARKER_LENGTH_MM:.2f} mm",
                (8, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.42,
                (255, 255, 255), 1, cv2.LINE_AA)
    if fps is not None:
        cv2.putText(frame, f"FPS: {fps:.1f}",
                    (8, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.42,
                    (120, 210, 120), 1, cv2.LINE_AA)
    cv2.putText(frame, "Q = Beenden  |  S = Screenshot",
                (8, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.38,
                (140, 140, 140), 1, cv2.LINE_AA)


# ── Konsolen-Ausgabe ──────────────────────────────────────────────────────────

def print_marker_info(marker_id, xyz, corners_2d):
    pts = corners_2d.reshape((4, 2)).astype(int)
    sep = "─" * 66
    print(f"\n  ┌─ Marker ID: {marker_id} {'─'*(52-len(str(marker_id)))}┐")
    print(f"  │  {'Ecke':<4}  {'Px X':>6}  {'Px Y':>6}  "
          f"{'X mm':>9}  {'Y mm':>9}  {'Z mm':>9}  │")
    print(f"  │  {sep}  │")
    for i, (px, py) in enumerate(pts):
        if xyz is not None:
            x3, y3, z3 = xyz[i]
            s = f"  {x3:+9.2f}  {y3:+9.2f}  {z3:+9.2f}"
        else:
            s = f"  {'n/a':>9}  {'n/a':>9}  {'n/a':>9}"
        print(f"  │  {CORNER_LABELS[i]:<4}  {px:>6}  {py:>6}{s}  │")
    print(f"  └{'─'*68}┘")


# ── Erkennungslogik ───────────────────────────────────────────────────────────

def process_frame(frame, detector, verbose=False):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = detector.detectMarkers(gray)

    if ids is None:
        return 0

    for i, marker_id in enumerate(ids.flatten()):
        c2d             = corners[i]
        xyz, rvec, tvec = compute_3d_corners(c2d)

        draw_marker(frame, c2d, marker_id, xyz)
        if rvec is not None:
            draw_axis(frame, rvec, tvec)
        if verbose:
            print_marker_info(marker_id, xyz, c2d)

    return len(ids)


# ── Kamera- und Bildmodus ─────────────────────────────────────────────────────

def run_camera(camera_idx, dict_name, detector):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print(f"[Fehler] Kamera {camera_idx} konnte nicht geöffnet werden.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[Info] Kamera {camera_idx} gestartet  ({W}×{H} px)")
    print(f"[Info] Wörterbuch   : {dict_name}")
    print(f"[Info] Marker-Länge : {MARKER_LENGTH_MM:.3f} mm")
    print( "[Info] Q = Beenden  |  S = Screenshot\n")

    fps      = 0.0
    prev_t   = time.time()
    prev_ids = set()
    shot_n   = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[Fehler] Kein Bild von Kamera.")
            break

        now    = time.time()
        fps    = 0.9 * fps + 0.1 / max(now - prev_t, 1e-6)
        prev_t = now

        # verbose nur wenn sich erkannte Marker-IDs ändern
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, ids_raw, _ = detector.detectMarkers(gray)
        cur_ids  = set(ids_raw.flatten().tolist()) if ids_raw is not None else set()
        verbose  = cur_ids != prev_ids
        prev_ids = cur_ids

        num = process_frame(frame, detector, verbose=verbose)
        draw_hud(frame, num, dict_name, fps)

        cv2.imshow("ArUco 3D Detektor  –  Kamera " + str(camera_idx), frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            shot_n += 1
            fname = f"aruco_3d_{shot_n:03d}.png"
            cv2.imwrite(fname, frame)
            print(f"[Info] Screenshot gespeichert: {fname}")

    cap.release()
    cv2.destroyAllWindows()
    print("\n[Info] Beendet.")


def run_image(image_path, dict_name, detector):
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"[Fehler] Bild '{image_path}' nicht lesbar.")
        sys.exit(1)

    print(f"[Info] Bild: {image_path}  |  {dict_name}\n")
    num = process_frame(frame, detector, verbose=True)
    print(f"\n  → {num} Marker erkannt." if num else "\n  → Keine Marker gefunden.")

    draw_hud(frame, num, dict_name)
    out = image_path.rsplit(".", 1)[0] + "_aruco3d.png"
    cv2.imwrite(out, frame)
    print(f"[Info] Ergebnis: {out}")
    cv2.imshow("ArUco 3D – " + image_path, frame)
    print("[Info] Beliebige Taste zum Schließen.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# ── Einstiegspunkt ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ArUco Marker Detektor – 3D XYZ Koordinaten via Kalibrierung"
    )
    parser.add_argument("--camera", type=int, default=4,
                        help="Kamera-Index (Standard: 4)")
    parser.add_argument("--dict", default="DICT_4X4_50",
                        choices=ARUCO_DICTS.keys(),
                        help="ArUco-Wörterbuch (Standard: DICT_4X4_50)")
    parser.add_argument("--image", type=str, default=None,
                        help="Pfad zu einem Einzelbild statt Kamera")
    args = parser.parse_args()

    aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICTS[args.dict])
    params     = cv2.aruco.DetectorParameters()
    detector   = cv2.aruco.ArucoDetector(aruco_dict, params)

    if args.image:
        run_image(args.image, args.dict, detector)
    else:
        run_camera(args.camera, args.dict, detector)


if __name__ == "__main__":
    main()