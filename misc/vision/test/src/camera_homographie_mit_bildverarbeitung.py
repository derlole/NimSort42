import cv2
import numpy as np

# =============================================================================
# PIXELKOORDINATEN DER 2D-CODE-ECKEN  (im Bild ablesen)
# Reihenfolge: oben-links, oben-rechts, unten-rechts, unten-links
# =============================================================================
pixel_punkte = np.array([
    [69, 62],   # Ecke 1 oben-links
    [113, 62],   # Ecke 2 oben-rechts
    [114, 109],   # Ecke 3 unten-rechts
    [70, 109],   # Ecke 4 unten-links
    [159, 61],
    [202, 61],
    [204, 107],
    [160, 108],
], dtype=np.float32)

# =============================================================================
# WELTKOORDINATEN IN MM  (am Förderband ausmessen, Ursprung = links unten)
# Reihenfolge muss dieselbe sein wie oben!
# =============================================================================
welt_punkte = np.array([
    [56, 25],   # Ecke 1 oben-links  [X_mm, Y_mm]
    [76, 25],   # Ecke 2 oben-rechts
    [76, 5],   # Ecke 3 unten-rechts
    [56, 5],   # Ecke 4 unten-links
    [98, 25],
    [118, 25], 
    [118, 5],
    [98, 5],
], dtype=np.float32)

# Homographie berechnen
H, _ = cv2.findHomography(pixel_punkte, welt_punkte)

# =============================================================================
# HILFSFUNKTION: Pixel -> Weltkoordinaten
# =============================================================================
def pixel_zu_welt(u, v):
    p = np.array([u, v, 1.0])
    w = H @ p
    w /= w[2]
    return round(w[0], 1), round(w[1], 1)

# =============================================================================
# HIER DEINE BILDVERARBEITUNG EINSETZEN
# -> schwerpunkte_pixel mit deinen echten Schwerpunkten befüllen
# =============================================================================

schwerpunkte_pixel = [
    # (u, v),   <- deine Schwerpunkte hier rein
]

# =============================================================================
# AUSGABE
# =============================================================================
for i, (u, v) in enumerate(schwerpunkte_pixel):
    x, y = pixel_zu_welt(u, v)
    print(f"Objekt {i+1}: Pixel ({u},{v})  ->  X={x} mm  Y={y} mm")