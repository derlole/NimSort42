# main_logic
POSITION_UNCORN: tuple[float, float, float] = (-0.16,-0.14, 0.07) #TODO: Werte in Weltkoordinaten anpassen
POSITION_CAT: tuple[float, float, float] = (-0.06, -0.14, 0.07)
INITIAL_POSITION: tuple[float, float, float] = (-0.01,-0.05, 0.02)
Z_PRE_POST_PICK: float = 0.08 #z-Höhe über Objekt für Pick-Preposition
Z_PICK: float = 0.095 #z-Höhe über Objekt für Pick-Position
GENERIC_PICK_PRE_POSITION: tuple[float, float, float] = (-0.01, -0.05, Z_PRE_POST_PICK) #TODO: Werte in Weltkoordinaten anpassen
SENTINEL: tuple[float, float, float] = (-1.0, -1.0, -1.0,-1)
ROBOT_REACH: float = -0.3 #maximale Reichweite des Roboters in x-Richtung, Werte in Weltkoordinaten anpassen

# TF_CONFIG
WORLD_TO_ROBOT_TRANSLATION: float = (0.29, -0.04, 0.083)

