import cv2

cap = cv2.VideoCapture(4)
cv2.namedWindow("FBI-Survailance-Cam", cv2.WINDOW_NORMAL)

# Linien definieren: (start_x, start_y), (end_x, end_y), farbe BGR, dicke
lines = [
    ((542,  171),  (356, 166),  (0, 0, 255), 2),   # kästichen 5x1
    ((356,  166),  (356,  120), (0, 0, 255), 2),   
    ((356, 120),  (543, 129), (0, 0, 255), 2),   
    ((543, 129), (542, 171), (0, 0, 255), 2),
    ((0, 0), (50, 50), (255, 0, 0), 2),   
]

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Alle Linien zeichnen
    for (start, end, color, thickness) in lines:
        cv2.line(frame, start, end, color, thickness)

    cv2.imshow("FBI-Survailance-Cam", frame)
    key = cv2.waitKey(1)

    if key == 27:
        break
    elif key == ord('f'):
        prop = cv2.getWindowProperty("FBI-Survailance-Cam", cv2.WND_PROP_FULLSCREEN)
        if prop == cv2.WINDOW_FULLSCREEN:
            cv2.setWindowProperty("FBI-Survailance-Cam", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
        else:
            cv2.setWindowProperty("FBI-Survailance-Cam", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

cap.release()
cv2.destroyAllWindows()