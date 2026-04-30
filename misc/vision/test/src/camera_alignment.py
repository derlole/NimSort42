import cv2

cap = cv2.VideoCapture(4)
cv2.namedWindow("FBI-Survailance-Cam", cv2.WINDOW_NORMAL)

# Linien definieren: (start_x, start_y), (end_x, end_y), farbe BGR, dicke
lines = [
    ((566,  107),  (375, 107),  (0, 0, 255), 1),   # kästichen 5x1
    ((375, 107),  (374,  60), (0, 0, 255), 1),   
    ((374, 60),  (566, 63), (0, 0, 255), 1),   
    ((566, 63), (566, 107), (0, 0, 255), 1),
    ((23, 307), (600, 275), (255, 0, 0), 2),
    ((16, 118), (566, 112), (255, 0, 0), 2),   
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