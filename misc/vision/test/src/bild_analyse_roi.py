import cv2
import numpy as np

# ---------------------------------------------------------
# 1. Kamera-Kalibrierungsdaten
# ---------------------------------------------------------
camera_matrix = np.array([
    [8551.027237070186, 0.0, 1097.9868366385667],
    [0.0, 7842.141565217346, 377.63303851765414],
    [0.0, 0.0, 1.0]
], dtype=np.float32)

dist_coeff = np.array([
    -2.452975486976177,
    19.573130834430437,
    0.056176108223266616,
    -0.04577371058464672,
    821.4645129965147
], dtype=np.float32)

# ---------------------------------------------------------
# 2. Bild einlesen
# ---------------------------------------------------------
image = cv2.imread("/home/louis/Sync/Studium/4._Semester/Robotik_Projekt/OpenCVTest/test/pictures/katze_4.jpg")
if image is None:
    raise ValueError("Bild konnte nicht geladen werden!")

# ---------------------------------------------------------
# 3. Bild entzerren
# ---------------------------------------------------------
h_img, w_img = image.shape[:2]
new_camera_matrix, _ = cv2.getOptimalNewCameraMatrix(
    camera_matrix, dist_coeff, (w_img, h_img), 1, (w_img, h_img)
)
undistorted = cv2.undistort(image, camera_matrix, dist_coeff, None, new_camera_matrix)

# ---------------------------------------------------------
# 4. ROI als Trapez mit 4 Punkten definieren
#    Reihenfolge: oben-links, oben-rechts, unten-rechts, unten-links
#    (im entzerrten Bild)
# ---------------------------------------------------------
roi_points = np.array([
    [10,  122],   # oben-links
    [630, 122],   # oben-rechts
    [630, 270],   # unten-rechts
    [10,  300],   # unten-links
], dtype=np.float32)

# Ausgabegröße des gewarpten (rektifizierten) ROI-Bildes berechnen
# Breite = max der oberen / unteren Kante
width_top  = np.linalg.norm(roi_points[1] - roi_points[0])
width_bot  = np.linalg.norm(roi_points[2] - roi_points[3])
roi_width  = int(max(width_top, width_bot))

# Höhe = max der linken / rechten Kante
height_left  = np.linalg.norm(roi_points[3] - roi_points[0])
height_right = np.linalg.norm(roi_points[2] - roi_points[1])
roi_height   = int(max(height_left, height_right))

# Ziel-Rechteck für den Warp
dst_points = np.array([
    [0,          0         ],
    [roi_width-1, 0         ],
    [roi_width-1, roi_height-1],
    [0,          roi_height-1],
], dtype=np.float32)

# Perspektivische Transformationsmatrix
M_warp = cv2.getPerspectiveTransform(roi_points, dst_points)
M_warp_inv = cv2.getPerspectiveTransform(dst_points, roi_points)   # für Rückprojektion

# Trapez-ROI in ein Rechteck entfalten
roi = cv2.warpPerspective(undistorted, M_warp, (roi_width, roi_height))

# ---------------------------------------------------------
# 5. Weiterverarbeitung (identisch wie vorher, jetzt auf gewarptem ROI)
# ---------------------------------------------------------
gray  = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
blur  = cv2.GaussianBlur(gray, (5, 5), 0)
_, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

result   = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contours = result[0] if len(result) == 2 else result[1]
contours = [cnt for cnt in contours if cv2.contourArea(cnt) >= 4500]
contours = sorted(
    contours,
    key=lambda cnt: cv2.moments(cnt)["m10"] / cv2.moments(cnt)["m00"],
    reverse=True
)

if not contours:
    raise RuntimeError("Keine Konturen im ROI gefunden.")

contour = contours[0]

print(f"\n{'='*50}")
print(f"  {len(contours)} Kontur(en) im ROI erkannt")
print(f"{'='*50}")

area       = cv2.contourArea(contour)
perimeter  = cv2.arcLength(contour, True)
compactness = (4 * np.pi * area) / (perimeter ** 2) if perimeter != 0 else 0

M = cv2.moments(contour)
if M["m00"] != 0:
    cx_roi = int(M["m10"] / M["m00"])
    cy_roi = int(M["m01"] / M["m00"])
else:
    cx_roi, cy_roi = 0, 0

# ---------------------------------------------------------
# 6. Schwerpunkt zurück ins entzerrte Gesamtbild projizieren
# ---------------------------------------------------------
pt_roi   = np.array([[[cx_roi, cy_roi]]], dtype=np.float32)
pt_global = cv2.perspectiveTransform(pt_roi, M_warp_inv)
cx = int(pt_global[0][0][0])
cy = int(pt_global[0][0][1])

nummer = 1
print(f"\n  Kontur #{nummer}:")
print(f"    Fläche:       {area:.2f} px²")
print(f"    Umfang:       {perimeter:.2f} px")
print(f"    Kompaktheit:  {compactness:.3f}")
print(f"    Schwerpunkt (global): ({cx}, {cy})")

# Kontur zurück ins Gesamtbild projizieren
contour_float  = contour.astype(np.float32).reshape(-1, 1, 2)
contour_global = cv2.perspectiveTransform(contour_float, M_warp_inv)
contour_global = contour_global.astype(np.int32)

cv2.drawContours(undistorted, [contour_global], -1, (0, 255, 0), 2)
cv2.circle(undistorted, (cx, cy), 5, (0, 0, 255), -1)
cv2.putText(undistorted, f"#{nummer}", (cx + 10, cy - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

print(f"\n{'='*50}\n")

# Trapez-ROI einzeichnen
cv2.polylines(undistorted, [roi_points.astype(np.int32)], isClosed=True,
              color=(255, 0, 255), thickness=2)

cv2.imshow("Ergebnis (entzerrt)", undistorted)
cv2.imshow("ROI Threshold", thresh)
cv2.waitKey(0)
cv2.destroyAllWindows()