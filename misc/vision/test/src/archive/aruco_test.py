"""
ArUco Marker Erkennung mit Live XYZ-Achsenanzeige
Benötigte Pakete: pip install opencv-contrib-python numpy
"""

import cv2
import numpy as np

# --- Kamera-Kalibrierung (Standardwerte – für echte Genauigkeit kalibrieren!) ---
def get_kamera_parameter(breite=640, hoehe=480):
    fx = fy = 800
    cx, cy = breite / 2, hoehe / 2
    kamera_matrix = np.array([[fx, 0, cx],
                               [0, fy, cy],
                               [0,  0,  1]], dtype=np.float64)
    verzerrung = np.zeros((4, 1))
    return kamera_matrix, verzerrung


def zeichne_achsen(frame, rvec, tvec, kamera_matrix, verzerrung, marker_laenge):
    """Zeichnet XYZ-Achsen auf den Marker."""
    l = marker_laenge * 0.6  # Achsenlänge

    achsen_punkte = np.float32([
        [0, 0, 0],   # Ursprung
        [l, 0, 0],   # X-Achse → Rot
        [0, l, 0],   # Y-Achse → Grün
        [0, 0, -l],  # Z-Achse → Blau (zeigt aus Marker heraus)
    ])

    bild_punkte, _ = cv2.projectPoints(achsen_punkte, rvec, tvec, kamera_matrix, verzerrung)
    bild_punkte = bild_punkte.reshape(-1, 2).astype(int)

    ursprung = tuple(bild_punkte[0])
    cv2.arrowedLine(frame, ursprung, tuple(bild_punkte[1]), (0,   0, 255), 3, tipLength=0.3)  # X → Rot
    cv2.arrowedLine(frame, ursprung, tuple(bild_punkte[2]), (0, 255,   0), 3, tipLength=0.3)  # Y → Grün
    cv2.arrowedLine(frame, ursprung, tuple(bild_punkte[3]), (255,  0,   0), 3, tipLength=0.3)  # Z → Blau

    # Beschriftungen
    cv2.putText(frame, "X", tuple(bild_punkte[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,   0, 255), 2)
    cv2.putText(frame, "Y", tuple(bild_punkte[2]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255,   0), 2)
    cv2.putText(frame, "Z", tuple(bild_punkte[3]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,  0,   0), 2)


def main():
    MARKER_LAENGE = 0.03   # Markergröße in Metern (30 mm)
    WOERTERBUCH   = cv2.aruco.DICT_4X4_50

    woerterbuch = cv2.aruco.getPredefinedDictionary(WOERTERBUCH)
    parameter   = cv2.aruco.DetectorParameters()
    detektor    = cv2.aruco.ArucoDetector(woerterbuch, parameter)

    kamera = cv2.VideoCapture(4)
    if not kamera.isOpened():
        print("❌ Kamera nicht gefunden!")
        return

    breite  = int(kamera.get(cv2.CAP_PROP_FRAME_WIDTH))
    hoehe   = int(kamera.get(cv2.CAP_PROP_FRAME_HEIGHT))
    kamera_matrix, verzerrung = get_kamera_parameter(breite, hoehe)

    print("✅ Kamera geöffnet. Drücke 'q' zum Beenden.")
    print(f"   Wörterbuch: DICT_4X4_50 | Markergröße: {MARKER_LAENGE*1000:.0f} mm | Kamera ID: 4")

    # Marker-Eckpunkte im 3D-Objektraum (einmal berechnen)
    halb = MARKER_LAENGE / 2
    obj_punkte = np.array([
        [-halb,  halb, 0],
        [ halb,  halb, 0],
        [ halb, -halb, 0],
        [-halb, -halb, 0],
    ], dtype=np.float32)

    while True:
        ret, frame = kamera.read()
        if not ret:
            break

        grau = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ecken, ids, _ = detektor.detectMarkers(grau)

        if ids is not None:
            cv2.aruco.drawDetectedMarkers(frame, ecken, ids)

            for i, (ecke, marker_id) in enumerate(zip(ecken, ids.flatten())):
                bild_punkte_2d = ecke[0].astype(np.float32)
                _, rvec, tvec = cv2.solvePnP(
                    obj_punkte, bild_punkte_2d, kamera_matrix, verzerrung
                )

                zeichne_achsen(frame, rvec, tvec, kamera_matrix, verzerrung, MARKER_LAENGE)

                # Position als Text anzeigen
                x, y, z = tvec.flatten()
                text = f"ID {marker_id}: X={x:.3f} Y={y:.3f} Z={z:.3f} m"
                cv2.putText(frame, text, (10, 30 + i * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        else:
            cv2.putText(frame, "Kein Marker erkannt", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow("ArUco XYZ-Achsen", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    kamera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()