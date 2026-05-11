import cv2

frame = cv2.imread("/home/louis/Sync/Studium/4._Semester/Robotik_Projekt/OpenCVTest/test/pictures/katze_4.jpg")

if frame is None:
    print("Fehler: Bild konnte nicht geladen werden!")
    exit()

# Linien definieren: (start_x, start_y), (end_x, end_y), farbe BGR, dicke
lines = [
    ((566, 107), (375, 107), (0, 0, 255), 1),   # kästchen 5x1
    ((375, 107), (374,  60), (0, 0, 255), 1),
    ((374,  60), (566,  63), (0, 0, 255), 1),
    ((566,  63), (566, 107), (0, 0, 255), 1),
    (( 23, 307), (600, 275), (255, 0, 0), 2),
    (( 16, 118), (566, 112), (255, 0, 0), 2),
]

while True:
    display = frame.copy()  # Kopie, damit Linien nicht aufeinander gestapelt werden

    for (start, end, color, thickness) in lines:
        cv2.line(display, start, end, color, thickness)

    cv2.imshow("Alignment", display)
    key = cv2.waitKey(1)

    if key == 27:  # ESC
        break
    elif key == ord('f'):
        prop = cv2.getWindowProperty("FBI-Survailance-Cam", cv2.WND_PROP_FULLSCREEN)
        if prop == cv2.WINDOW_FULLSCREEN:
            cv2.setWindowProperty("FBI-Survailance-Cam", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
        else:
            cv2.setWindowProperty("FBI-Survailance-Cam", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

cv2.destroyAllWindows()