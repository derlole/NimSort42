import cv2

cap = cv2.VideoCapture(4)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
cap.set(cv2.CAP_PROP_FPS, 30)

# Prüfen ob Full HD geklappt hat
width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
print(f"Auflösung: {int(width)}x{int(height)}")

cv2.namedWindow("FBI-Survailance-Cam", cv2.WINDOW_NORMAL)
cv2.resizeWindow("FBI-Survailance-Cam", 1920, 1080)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("FBI-Survailance-Cam", frame)
    key = cv2.waitKey(1)

    if key == 27:       # ESC = Beenden
        break
    elif key == ord('f'):  # F = Vollbild togglen
        prop = cv2.getWindowProperty("FBI-Survailance-Cam", cv2.WND_PROP_FULLSCREEN)
        if prop == cv2.WINDOW_FULLSCREEN:
            cv2.setWindowProperty("FBI-Survailance-Cam", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
        else:
            cv2.setWindowProperty("FBI-Survailance-Cam", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

cap.release()
cv2.destroyAllWindows()