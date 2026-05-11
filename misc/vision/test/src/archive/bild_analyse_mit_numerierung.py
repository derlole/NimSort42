import cv2
import numpy as np

# ---------------------------------------------------------
# 1. Kamera-Kalibrierungsdaten
# ---------------------------------------------------------
camera_matrix = np.array([
    [2710.666860974311, 0.0, 367.8525523358933],
    [0.0, 2766.057464263328, 245.68063913559047],
    [0.0, 0.0, 1.0]
], dtype=np.float32)

dist_coeff = np.array([
    -1.4668410355213393,
    -19.46254234953102,
    -0.0022364037989029096,
    -0.03440200232868026,
    450.2793784546618
], dtype=np.float32)

# ---------------------------------------------------------
# 2. Bild einlesen
# ---------------------------------------------------------
image = cv2.imread("/home/louis/Sync/Studium/4._Semester/Robotik_Projekt/OpenCVTest/test/pictures/bild_105.jpg")

if image is None:
    raise ValueError("Bild konnte nicht geladen werden!")

# ---------------------------------------------------------
# 3. Bild entzerren
# ---------------------------------------------------------
h, w = image.shape[:2]

# Optimierte neue Kameramatrix (optional, aber empfohlen)
new_camera_matrix, _ = cv2.getOptimalNewCameraMatrix(
    camera_matrix, dist_coeff, (w, h), 1, (w, h)
)

# Entzerrtes Bild erzeugen
undistorted = cv2.undistort(image, camera_matrix, dist_coeff, None, new_camera_matrix)

# ---------------------------------------------------------
# 4. ROI Definition (x, y, breite, höhe) – jetzt im ENTZERRTEN Bild!
# ---------------------------------------------------------
#interest_roi = (10, 113, 615, 194)
interest_roi = (10, 165, 615, 180) # nur für testbilder 

x, y, w, h = interest_roi

roi = undistorted[y:y+h, x:x+w]

# ---------------------------------------------------------
# 5. Weiterverarbeitung wie bisher
# ---------------------------------------------------------
gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
blur = cv2.GaussianBlur(gray, (5, 5), 0)
_, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

result = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contours = result[0] if len(result) == 2 else result[1]

contours = [cnt for cnt in contours if cv2.contourArea(cnt) >= 4500]
contours = sorted(contours, key=lambda cnt: cv2.moments(cnt)["m10"] / cv2.moments(cnt)["m00"], reverse=True)

if not contours:
    raise RuntimeError("Keine Konturen im ROI gefunden.")

contour = contours[0]

print(f"\n{'='*50}")
print(f"  {len(contours)} Kontur(en) im ROI erkannt")
print(f"{'='*50}")


area = cv2.contourArea(contour)
perimeter = cv2.arcLength(contour, True)
compactness = (4 * np.pi * area) / (perimeter ** 2) if perimeter != 0 else 0

M = cv2.moments(contour)
if M["m00"] != 0:
    cx_roi = int(M["m10"] / M["m00"])
    cy_roi = int(M["m01"] / M["m00"])
else:
    cx_roi, cy_roi = 0, 0

# Schwerpunkt zurück ins Gesamtbild (ENTZERRT)
cx = cx_roi + x
cy = cy_roi + y

nummer = 1
print(f"\n  Kontur #{nummer}:")
print(f"    Fläche:       {area:.2f} px²")
print(f"    Umfang:       {perimeter:.2f} px")
print(f"    Kompaktheit:  {compactness:.3f}")
print(f"    Schwerpunkt:  ({cx}, {cy})")

contour_global = contour + np.array([[x, y]])
cv2.drawContours(undistorted, [contour_global], -1, (0, 255, 0), 2)
cv2.circle(undistorted, (cx, cy), 5, (0, 0, 255), -1)
cv2.putText(undistorted, f"#{nummer}", (cx + 10, cy - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

print(f"\n{'='*50}\n")

# ROI anzeigen
cv2.rectangle(undistorted, (x, y), (x + w, y + h), (255, 0, 255), 2)

cv2.imshow("Ergebnis (entzerrt)", undistorted)
cv2.imshow("ROI Threshold", thresh)

cv2.waitKey(0)
cv2.destroyAllWindows()
