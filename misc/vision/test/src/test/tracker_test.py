import cv2

# Kamera öffnen (ID 4)
cap = cv2.VideoCapture(4)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Graustufen
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Threshold (weiß = 255, schwarz = 0)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    # Konturen finden
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Nur die 2 größten Konturen nehmen (deine Objekte)
    contours = sorted(contours, key=cv2.contourArea, reverse=True) #[:2] <-- Anzahl der zu verfolgenden Objekte begrenzen

    for cnt in contours:
        # Kontur zeichnen
        cv2.drawContours(frame, [cnt], -1, (0, 255, 0), 2)

        # Mittelpunkt berechnen
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

    # Anzeigen
    cv2.imshow("Frame", frame)
    cv2.imshow("Threshold", thresh)

    # ESC zum Beenden
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()