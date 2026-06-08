import numpy as np

# feature_detection
LABEL_MAP = {0: "einhorn", 1: "katze", 2: "kreis", 3: "quadrat"}
MIN_CONTOUR_AREA = 4500

# opencv_pipeline
CAMERA_INDEX = 4
MIN_CONTOUR_AREA = 4500
Z_W_CONSTANT_IN_MM = 2.0
MIN_OTSU_THRESHOLD = 90


# Trapez-ROI: vier Eckpunkte im Uhrzeigersinn (oben-links, oben-rechts, unten-rechts, unten-links)
ROI_TRAPEZ = np.array([
    [14,  121],   # oben-links
    [602, 116],   # oben-rechts
    [602, 272],   # unten-rechts
    [14,  304],   # unten-links
], dtype=np.int32)

PIXEL_PUNKTE = np.array([
    [66, 131],   # Ecke 1 oben-links
    [109, 131],  # Ecke 2 oben-rechts
    [109, 178],  # Ecke 3 unten-rechts
    [66, 178],   # Ecke 4 unten-links
    [153, 129],  # 2. Quadrat oben-links
    [195, 129],
    [195, 175],
    [153, 176], 
    [238, 128],  # 3. Quadrat oben-links
    [278, 127],
    [279, 173],
    [239, 174], 
    [321, 127],   # 4. Quadrat oben-links
    [359, 127],
    [360, 172],
    [321, 172],  
    [400, 126],   # 5. Quadrat oben-links
    [437, 126],
    [438, 170],
    [401, 172],  
                  # 6. Quadrat oben-links
], dtype=np.float32)

WELT_PUNKTE = np.array([
    [59, 0],      # Ecke 1 oben-links  [X_mm, Y_mm]
    [78.40, 0],   # Ecke 2 oben-rechts
    [78.40, -20], # Ecke 3 unten-rechts
    [59, -20],    # Ecke 4 unten-links
    [97.7, 0],    # 2. Quadrat oben-links
    [117.18, 0],
    [117.18, -20],
    [97.7, -20],   
    [136.3, 0],   # 3. Quadrant oben-links
    [155.8, 0],
    [155.8, -20],
    [136.3, -20], 
    [175.1, 0],    # 4. Quadrant oben-links
    [194.3, 0],
    [194.3, -20],
    [175.1, -20],  
    [213.8, 0],    # 5. Quadrant oben-links
    [233.3, 0],
    [233.3, -20],
    [213.8, -20],  
                  # 6. Quadrant oben-links
], dtype=np.float32)


# Pickpunkt-Offset in Pixeln (Abstand vom Schwerpunkt zum tatsächlichen Greifpunkt)
PICK_OFFSET_PX = 7

# plausibility_check
X_MIN = 0.0
X_MAX = 0.6 
Y_MIN = 0.02
Y_MAX = 0.13

DEFAULT_SPEED_ESTIMATION = 0.01