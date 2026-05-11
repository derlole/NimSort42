import numpy as np
import cv2
import yaml
import time

# Camera Parameter
CAMERA_ID = 4
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1080
CAMERA_FPS = 30

# ChArUco Board Parameter
SQUARES_X = 7
SQUARES_Y = 5
BOARD_WIDTH = 170  # mm
BOARD_HEIGHT = 119  # mm

# Berechne Quadratgröße
SQUARE_LENGTH = BOARD_WIDTH / SQUARES_X
MARKER_LENGTH = SQUARE_LENGTH * 0.75

# ChArUco Board erstellen
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
board = cv2.aruco.CharucoBoard(
    (SQUARES_X, SQUARES_Y),
    SQUARE_LENGTH,
    MARKER_LENGTH,
    aruco_dict
)
charuco_detector = cv2.aruco.CharucoDetector(board)

# Datensammlungen
all_charuco_corners = []
all_charuco_ids = []
image_size = None

# Kamera initialisieren
cap = cv2.VideoCapture(CAMERA_ID)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

# Auflösung prüfen
actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Kamera Auflösung: {actual_width}x{actual_height}")
if actual_width != CAMERA_WIDTH or actual_height != CAMERA_HEIGHT:
    print(f"⚠️  WARNUNG: Kamera läuft nicht in Full HD!")
    print(f"   Erwartet: {CAMERA_WIDTH}x{CAMERA_HEIGHT}")
    print(f"   Tatsächlich: {actual_width}x{actual_height}")
    print(f"   Kalibrierung wird trotzdem mit {actual_width}x{actual_height} durchgeführt.")
else:
    print(f"✅ Full HD aktiv: {actual_width}x{actual_height}")

found = 0
required_images = 20

print(f"\nSammle {required_images} Kalibrierungsbilder...")
print("Bewege das ChArUco Board in verschiedene Positionen und Winkel")
print("Drücke 'q' zum Abbrechen")

last_capture_time = 0

while found < required_images:
    ret, img = cap.read()
    if not ret:
        print("Fehler beim Lesen der Kamera")
        break

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if image_size is None:
        image_size = tuple(gray.shape[::-1])
        print(f"Bildgröße für Kalibrierung: {image_size}")

    # ChArUco Ecken detektieren
    charuco_corners, charuco_ids, marker_corners, marker_ids = charuco_detector.detectBoard(gray)

    # Anzeige-Frame vorbereiten (skaliert auf 1280x720 für die Anzeige)
    display_scale = 0.667
    display = cv2.resize(img.copy(), (int(img.shape[1] * display_scale), int(img.shape[0] * display_scale)))

    current_time = time.time()

    if charuco_corners is not None and len(charuco_corners) > 6:
        # Erkannte Ecken für Anzeige skalieren
        scaled_corners = charuco_corners * display_scale
        scaled_marker_corners = [c * display_scale for c in marker_corners] if marker_corners else None

        if scaled_marker_corners:
            cv2.aruco.drawDetectedMarkers(display, scaled_marker_corners, marker_ids)
        cv2.aruco.drawDetectedCornersCharuco(display, scaled_corners, charuco_ids, (0, 255, 0))

        # Automatisch erfassen nach 2 Sekunden Cooldown
        if current_time - last_capture_time >= 2.0:
            all_charuco_corners.append(charuco_corners)
            all_charuco_ids.append(charuco_ids)
            found += 1
            last_capture_time = current_time
            print(f'Bild {found}/{required_images} erfasst - {len(charuco_corners)} Ecken gefunden')

        cv2.rectangle(display, (0, 0), (display.shape[1]-1, display.shape[0]-1), (0, 255, 0), 4)
        status_color = (0, 255, 0)
        status_text = f"Board erkannt: {len(charuco_corners)} Ecken"
    else:
        if marker_corners:
            scaled_marker_corners = [c * display_scale for c in marker_corners]
            cv2.aruco.drawDetectedMarkers(display, scaled_marker_corners, marker_ids)

        cv2.rectangle(display, (0, 0), (display.shape[1]-1, display.shape[0]-1), (0, 0, 255), 4)
        status_color = (0, 0, 255)
        status_text = "Board nicht erkannt"

    # Cooldown-Balken
    if last_capture_time > 0:
        elapsed = current_time - last_capture_time
        cooldown_ratio = min(elapsed / 2.0, 1.0)
        bar_width = int(display.shape[1] * cooldown_ratio)
        cv2.rectangle(display, (0, display.shape[0]-10), (bar_width, display.shape[0]), (0, 200, 255), -1)

    # Status-Overlay
    overlay = display.copy()
    cv2.rectangle(overlay, (0, 0), (display.shape[1], 80), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, display, 0.5, 0, display)

    cv2.putText(display, status_text, (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
    cv2.putText(display, f"Erfasst: {found}/{required_images}", (10, 55),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(display, f"Kalibrierung: {actual_width}x{actual_height}", (10, display.shape[0]-20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 0), 1)

    cv2.imshow("ChArUco Kalibrierung", display)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Abgebrochen.")
        break

cap.release()
cv2.destroyAllWindows()

if found < required_images:
    print("Nicht genug Bilder gesammelt. Kalibrierung abgebrochen.")
    exit()

print("\nStarte Kalibrierung...")

# 3D Objektpunkte für jeden Frame berechnen
all_object_points = []
all_image_points = []
for corners, ids in zip(all_charuco_corners, all_charuco_ids):
    object_points, image_points = board.matchImagePoints(corners, ids)
    all_object_points.append(object_points)
    all_image_points.append(image_points)

# Kalibrierung durchführen
ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
    objectPoints=all_object_points,
    imagePoints=all_image_points,
    imageSize=image_size,
    cameraMatrix=None,
    distCoeffs=None
)

if ret:
    print(f"\nKalibrierung erfolgreich!")
    print(f"Reprojection Error: {ret:.4f} Pixel")

    data = {
        'camera_matrix': np.asarray(camera_matrix).tolist(),
        'dist_coeff': np.asarray(dist_coeffs).tolist(),
        'reprojection_error': float(ret),
        'image_size': {
            'width': image_size[0],
            'height': image_size[1]
        },
        'board_config': {
            'squares_x': SQUARES_X,
            'squares_y': SQUARES_Y,
            'square_length': float(SQUARE_LENGTH),
            'marker_length': float(MARKER_LENGTH)
        }
    }

    with open("charuco_cali_bild.yaml", "w") as f:
        yaml.dump(data, f)

    print("\nKamera-Matrix:")
    print(camera_matrix)
    print("\nVerzerrungskoeffizienten:")
    print(dist_coeffs)
    print(f"\nGespeichert für Auflösung: {image_size[0]}x{image_size[1]}")
    print("Kalibrierung in 'charuco_cali_bild.yaml' gespeichert!")
else:
    print("Kalibrierung fehlgeschlagen!")