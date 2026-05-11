"""
ArUco Marker Pose-Erkennung
Kamera = Ursprung (0,0,0)
Gibt aus: X, Y, Z (in Metern), Roll, Pitch, Yaw (in Grad), Diagonalabstand
Speichert beim Beenden in: aruco_pose.yaml

Aufbau: Kamera schaut von oben schräg auf Förderband
"""

import cv2
import numpy as np
import yaml
import math
from datetime import datetime

# ---------------------------------------------------------------------------
# Kamera-Kalibrierung
# ---------------------------------------------------------------------------
KAMERA_MATRIX = np.array([
    [8551.027237070186,    0.0,             1097.9868366385667],
    [   0.0,           7842.141565217346,    377.63303851765414],
    [   0.0,              0.0,               1.0              ]
], dtype=np.float64)

VERZERRUNG = np.array([[
    -2.452975486976177,
    19.573130834430437,
     0.056176108223266616,
    -0.04577371058464672,
   821.4645129965147
]], dtype=np.float64)

REPROJEKTIONSFEHLER = 1.2400154511513628
BILD_GROESSE        = (1920, 1080)   # width, height
MARKER_LAENGE       = 0.03           # 30 mm → Meter
KAMERA_ID           = 4
YAML_DATEI          = "aruco_pose.yaml"

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def rvec_zu_euler(rvec):
    """Rotationsvektor → Roll, Pitch, Yaw in Grad (ZYX-Konvention)."""
    R, _ = cv2.Rodrigues(rvec)
    sy = math.sqrt(R[0, 0]**2 + R[1, 0]**2)
    if sy > 1e-6:
        roll  = math.atan2( R[2, 1], R[2, 2])
        pitch = math.atan2(-R[2, 0], sy)
        yaw   = math.atan2( R[1, 0], R[0, 0])
    else:
        roll  = math.atan2(-R[1, 2], R[1, 1])
        pitch = math.atan2(-R[2, 0], sy)
        yaw   = 0.0
    return math.degrees(roll), math.degrees(pitch), math.degrees(yaw)


def zeichne_achsen(frame, rvec, tvec, kmatrix, laenge=MARKER_LAENGE):
    """XYZ-Achsen auf Marker zeichnen (Kamera = Nullpunkt)."""
    l = laenge * 0.7
    punkte_3d = np.float32([[0,0,0],[l,0,0],[0,l,0],[0,0,-l]])
    pts, _    = cv2.projectPoints(punkte_3d, rvec, tvec, kmatrix, np.zeros((4,1)))
    pts       = pts.reshape(-1, 2).astype(int)
    o = tuple(pts[0])
    cv2.arrowedLine(frame, o, tuple(pts[1]), (0,   0, 255), 3, tipLength=0.25)  # X Rot
    cv2.arrowedLine(frame, o, tuple(pts[2]), (0, 255,   0), 3, tipLength=0.25)  # Y Grün
    cv2.arrowedLine(frame, o, tuple(pts[3]), (255,  0,   0), 3, tipLength=0.25) # Z Blau
    for p, label, color in zip(pts[1:], ["X","Y","Z"],
                                [(0,0,255),(0,255,0),(255,0,0)]):
        cv2.putText(frame, label, tuple(p), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)


def zeichne_hud(frame, marker_id, x, y, z, abstand, roll, pitch, yaw, idx):
    """Positions- und Winkelinfo als HUD einblenden."""
    y0 = 20 + idx * 130   # etwas mehr Platz wegen 5. Zeile
    def t(zeile, text, farbe=(240, 240, 100)):
        cv2.putText(frame, text, (10, y0 + zeile * 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, farbe, 2)

    # Einzelkomponenten für die Diagonalabstand-Formel
    # diag = sqrt(X² + Y² + Z²)  – identisch mit np.linalg.norm(tvec)
    t(0, f"[ Marker ID {marker_id} ]",                           (180, 180, 255))
    t(1, f"X={x:+.4f}m  Y={y:+.4f}m  Z={z:+.4f}m")
    t(2, f"Diagonalabstand (sqrt(X²+Y²+Z²)): {abstand:.4f} m",  (0, 230, 230))
    t(3, f"  -> X²+Y²+Z² = {x**2+y**2+z**2:.6f} m²",           (0, 180, 180))
    t(4, f"Roll={roll:+.1f}  Pitch={pitch:+.1f}  Yaw={yaw:+.1f}  [deg]",
                                                                  (150, 255, 150))


def speichere_yaml(daten):
    ausgabe = {
        "aufnahme_zeitpunkt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "koordinatensystem":  "Kamera = Ursprung (0,0,0), Z zeigt von Kamera weg",
        "einheiten":          {"position": "Meter", "winkel": "Grad"},
        "kalibrierung": {
            "reprojection_error_px": REPROJEKTIONSFEHLER,
            "bild_groesse":          f"{BILD_GROESSE[0]}x{BILD_GROESSE[1]}",
        },
        "marker": daten
    }
    with open(YAML_DATEI, "w") as f:
        yaml.dump(ausgabe, f, default_flow_style=False,
                  allow_unicode=True, sort_keys=False)
    print(f"✅  Gespeichert → {YAML_DATEI}")


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------
def main():
    woerterbuch = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    detektor    = cv2.aruco.ArucoDetector(
                      woerterbuch, cv2.aruco.DetectorParameters())

    kamera = cv2.VideoCapture(KAMERA_ID)
    if not kamera.isOpened():
        print(f"❌  Kamera {KAMERA_ID} nicht gefunden!")
        return

    # Auflösung auf Kalibrierungsgröße setzen (1920x1080)
    kamera.set(cv2.CAP_PROP_FRAME_WIDTH,  BILD_GROESSE[0])
    kamera.set(cv2.CAP_PROP_FRAME_HEIGHT, BILD_GROESSE[1])
    w = int(kamera.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(kamera.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"   Kameraauflösung: {w}x{h}  (kalibriert auf {BILD_GROESSE[0]}x{BILD_GROESSE[1]})")

    # Optimierte Kameramatrix für entzerrtes Bild
    neue_matrix, roi = cv2.getOptimalNewCameraMatrix(
        KAMERA_MATRIX, VERZERRUNG, (w, h), alpha=1, newImgSize=(w, h))

    # 3D-Eckpunkte des Markers im Objektkoordinatensystem
    halb = MARKER_LAENGE / 2
    obj_punkte = np.array([
        [-halb,  halb, 0],
        [ halb,  halb, 0],
        [ halb, -halb, 0],
        [-halb, -halb, 0],
    ], dtype=np.float32)

    letzte_posen = {}   # {marker_id: {...}}  immer aktuellster Wert

    print(f"✅  Kamera {KAMERA_ID} gestartet | Marker: {MARKER_LAENGE*1000:.0f} mm")
    print(f"   Kalibrierung: Reprojektionsfehler = {REPROJEKTIONSFEHLER:.4f} px")
    print("   Drücke  'q'  zum Beenden und Speichern.")

    while True:
        ret, frame = kamera.read()
        if not ret:
            print("❌  Kein Kamerabild!")
            break

        # Verzerrung korrigieren (wichtig für genaue Pose!)
        frame = cv2.undistort(frame, KAMERA_MATRIX, VERZERRUNG, None, neue_matrix)

        grau = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ecken, ids, _ = detektor.detectMarkers(grau)

        if ids is not None:
            cv2.aruco.drawDetectedMarkers(frame, ecken, ids)

            for idx, (ecke, marker_id) in enumerate(zip(ecken, ids.flatten())):
                bild_pts = ecke[0].astype(np.float32)

                # Pose lösen: tvec = Position des Markers relativ zur Kamera
                ok, rvec, tvec = cv2.solvePnP(
                    obj_punkte, bild_pts, neue_matrix, np.zeros((4,1)),
                    flags=cv2.SOLVEPNP_IPPE_SQUARE
                )
                if not ok:
                    continue

                zeichne_achsen(frame, rvec, tvec, neue_matrix)

                x, y, z = tvec.flatten()

                # Diagonalabstand = euklidische Norm = sqrt(X² + Y² + Z²)
                abstand = float(np.linalg.norm(tvec))

                roll, pitch, yaw = rvec_zu_euler(rvec)

                zeichne_hud(frame, marker_id, x, y, z,
                            abstand, roll, pitch, yaw, idx)

                # Konsolenausgabe
                print(f"  Marker {marker_id:2d} | "
                      f"X={x:+.4f}  Y={y:+.4f}  Z={z:+.4f} m | "
                      f"Diagonalabstand={abstand:.4f} m")

                letzte_posen[int(marker_id)] = {
                    "position_m": {
                        "x": round(float(x), 5),
                        "y": round(float(y), 5),
                        "z": round(float(z), 5),
                    },
                    "diagonalabstand_kamera_m": round(abstand, 5),   # ← umbenannt
                    "rotation_deg": {
                        "roll":  round(roll,  3),
                        "pitch": round(pitch, 3),
                        "yaw":   round(yaw,   3),
                    }
                }
        else:
            cv2.putText(frame, "Kein Marker erkannt", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 60, 255), 2)

        cv2.imshow("ArUco Pose  |  Kamera = (0,0,0)  |  'q' = Beenden", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    kamera.release()
    cv2.destroyAllWindows()

    if letzte_posen:
        yaml_daten = [{"id": mid, **pose}
                      for mid, pose in sorted(letzte_posen.items())]
        speichere_yaml(yaml_daten)
    else:
        print("⚠️   Keine Marker erkannt – nichts gespeichert.")


if __name__ == "__main__":
    main()