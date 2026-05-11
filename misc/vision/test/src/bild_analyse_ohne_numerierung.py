import cv2
import numpy as np

# 1. Bild einlesen
image = cv2.imread("/home/louis/Sync/Studium/4._Semester/Robotik_Projekt/OpenCVTest/test/pictures/bild_105.jpg")

# 2. In Graustufen umwandeln
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 3. Glätten (Rauschen reduzieren)
blur = cv2.GaussianBlur(gray, (5, 5), 0)

# 4. Threshold (helle Objekte auf dunklem Hintergrund)
_, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# 5. Konturen finden
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[:2]

# Durch alle Konturen gehen
for contour in contours:
    
    # 7. Fläche berechnen
    area = cv2.contourArea(contour)
    
    # Kleine Objekte ignorieren (optional)
    if area < 50:
        continue
    
    # 8. Umfang berechnen
    perimeter = cv2.arcLength(contour, True)
    
    # 9. Kompaktheit berechnen
    if perimeter != 0:
        compactness = (4 * np.pi * area) / (perimeter ** 2)
    else:
        compactness = 0
    
    # 10. Schwerpunkt berechnen
    M = cv2.moments(contour)
    
    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
    else:
        cx, cy = 0, 0
    
    # Ergebnisse ausgeben
    print(f"Fläche: {area:.2f}, Umfang: {perimeter:.2f}, Kompaktheit: {compactness:.3f}")
    print(f"Schwerpunkt: ({cx}, {cy})")
    
    # Kontur zeichnen
    cv2.drawContours(image, [contour], -1, (0, 255, 0), 2)
    
    # Schwerpunkt zeichnen
    cv2.circle(image, (cx, cy), 5, (0, 0, 255), -1)

# Ergebnis anzeigen
cv2.imshow("Ergebnis", image)
cv2.imshow("Threshold", thresh)

cv2.waitKey(0)
cv2.destroyAllWindows()