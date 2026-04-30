import cv2
import numpy as np

# =============================================================================
# SCHRITT 1: KAMERABILD LADEN
# =============================================================================

bild_pfad = "/home/louis/Sync/Studium/4._Semester/Robotik_Projekt/OpenCVTest/test/pictures/katze_4.jpg"   # <-- HIER deinen Bildpfad eintragen
bild = cv2.imread(bild_pfad)


# =============================================================================
# SCHRITT 2: PIXELKOORDINATEN DER 2D-CODE-ECKEN
#            (aus dem Bild ablesen z.B. mit Paint oder dem Hilfsskript unten)
#
#            Reihenfolge der Ecken:
#
#            Ecke1 ------- Ecke2
#              |               |
#            Ecke4 ------- Ecke3
# =============================================================================

pixel_punkte = np.array([
    [0,   0],    # <-- HIER Ecke 1 eintragen  (oben links)   z.B. [245, 130]
    [0,   0],    # <-- HIER Ecke 2 eintragen  (oben rechts)  z.B. [289, 128]
    [0,   0],    # <-- HIER Ecke 3 eintragen  (unten rechts) z.B. [291, 172]
    [0,   0],    # <-- HIER Ecke 4 eintragen  (unten links)  z.B. [247, 174]
], dtype=np.float32)


# =============================================================================
# SCHRITT 3: WELTKOORDINATEN DER 2D-CODE-ECKEN IN MILLIMETER
#            (am Förderband mit Maßband vom Ursprung messen)
#            Ursprung = links unten am Förderband
#
#            Reihenfolge muss dieselbe sein wie bei den Pixelpunkten oben!
# =============================================================================

welt_punkte = np.array([
    [0,   0],    # <-- HIER Ecke 1 eintragen  z.B. [50, 100]  (X mm, Y mm)
    [0,   0],    # <-- HIER Ecke 2 eintragen  z.B. [90, 100]
    [0,   0],    # <-- HIER Ecke 3 eintragen  z.B. [90,  60]
    [0,   0],    # <-- HIER Ecke 4 eintragen  z.B. [50,  60]
], dtype=np.float32)


# =============================================================================
# SCHRITT 4: HOMOGRAPHIE BERECHNEN  (einmalig, nichts ändern)
# =============================================================================

H, mask = cv2.findHomography(pixel_punkte, welt_punkte)
print("Homographie berechnet:")
print(H)


# =============================================================================
# SCHRITT 5: HILFSFUNKTION – PIXEL ZU WELTKOORDINATEN
# =============================================================================

def pixel_zu_welt(pixel_punkt, H):
    """
    Rechnet einen Bildpunkt (u, v) in Weltkoordinaten (X mm, Y mm) um.
    pixel_punkt: Tupel (u, v)
    H:           Homographiematrix
    Rückgabe:    (X_mm, Y_mm)
    """
    p = np.array([pixel_punkt[0], pixel_punkt[1], 1.0])
    welt = H @ p
    welt /= welt[2]   # Normierung (homogene Koordinaten)
    return round(welt[0], 1), round(welt[1], 1)


# =============================================================================
# SCHRITT 6: HIER DEINE BILDVERARBEITUNG EINBINDEN
#            Ersetze die Beispiel-Schwerpunkte durch deine echten Ergebnisse
# =============================================================================

# Beispiel-Schwerpunkte (Pixel) – durch deine Bildverarbeitung ersetzen!
schwerpunkte_pixel = [
    (320, 240),   # Objekt 1 – Platzhalter
    (150, 300),   # Objekt 2 – Platzhalter
]


# =============================================================================
# SCHRITT 7: AUSGABE DER WELTKOORDINATEN
# =============================================================================

print("\n--- Erkannte Objekte ---")
for i, sp in enumerate(schwerpunkte_pixel):
    x_mm, y_mm = pixel_zu_welt(sp, H)
    print(f"Objekt {i+1}: Pixel {sp}  →  Welt X={x_mm} mm  Y={y_mm} mm")

    # Visualisierung im Bild
    cv2.circle(bild, (int(sp[0]), int(sp[1])), 6, (0, 255, 0), -1)
    cv2.putText(bild,
                f"X={x_mm:.0f} Y={y_mm:.0f} mm",
                (int(sp[0]) + 10, int(sp[1])),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

cv2.imshow("Ergebnis", bild)
cv2.waitKey(0)
cv2.destroyAllWindows()


# =============================================================================
# HILFSSKRIPT – PIXELKOORDINATEN AUS BILD ABLESEN
# Diesen Block separat ausführen um Pixelkoordinaten zu bestimmen!
# =============================================================================

def pixelkoordinaten_bestimmen(bild_pfad):
    """
    Klicke auf die 4 Ecken des 2D-Codes im Bild.
    Die Pixelkoordinaten werden in der Konsole ausgegeben.
    """
    bild = cv2.imread(bild_pfad)
    klicks = []

    def maus_klick(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            klicks.append((x, y))
            cv2.circle(bild, (x, y), 5, (0, 0, 255), -1)
            cv2.putText(bild, f"Ecke {len(klicks)}: ({x},{y})",
                        (x + 8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.imshow("Klicke auf die 4 Ecken des 2D-Codes", bild)
            print(f"Ecke {len(klicks)}: Pixel = ({x}, {y})")
            if len(klicks) == 4:
                print("\nAlle 4 Ecken erfasst!")
                print("Trage diese Werte in pixel_punkte ein:")
                for k in klicks:
                    print(f"    {list(k)},")

    cv2.imshow("Klicke auf die 4 Ecken des 2D-Codes", bild)
    cv2.setMouseCallback("Klicke auf die 4 Ecken des 2D-Codes", maus_klick)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# Zum Aktivieren diese Zeile einkommentieren:
pixelkoordinaten_bestimmen(bild_pfad)