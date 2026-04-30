import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt

def flush_camera_buffer(cam, n=5):
    """Kamerabuffer leeren durch mehrfaches Lesen."""
    for _ in range(n):
        cam.grab()

def capture_image(cam, counter):
    """Buffer leeren, dann ein frisches Bild aufnehmen und speichern."""
    flush_camera_buffer(cam)
    success, frame = cam.read()
    if not success:
        print("Fehler: Kein Bild empfangen.")
        return counter

    filename = f"arucoboard_{counter}.jpg"
    cv.imwrite(filename, frame)
    print(f"Bild gespeichert: {filename}")

    # Bild anzeigen (BGR -> RGB für matplotlib)
    frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
   # plt.imshow(frame_rgb)
    plt.title(filename)
    plt.axis('off')
    plt.pause(0.5)   # kurz anzeigen ohne zu blockieren
    plt.clf()

    return counter + 1

def main():
    cam = cv.VideoCapture(4)
    if not cam.isOpened():
        print("Fehler: Kamera konnte nicht geöffnet werden.")
        return

    plt.ion()  # interaktiver Modus – Fenster bleibt offen
    counter = 1

    print("Drücke ENTER um ein Bild aufzunehmen. 'q' + ENTER zum Beenden.")

    try:
        while True:
            user_input = input("> ")
            if user_input.strip().lower() == 'q':
                print("Programm beendet.")
                break
            counter = capture_image(cam, counter)
    finally:
        cam.release()
        #plt.ioff()
        #plt.show()

if __name__ == "__main__":
    main()


    