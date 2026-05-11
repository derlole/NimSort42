

X_MIN = 0.0
X_MAX = 0.4 #TODO define limit and document it. According issue: #69

Y_MIN = 0.02
Y_MAX = 0.13 


class PlausibilityCheck:
    """Klasse zur Prüfung der Plausibilität von Koordinaten."""
    
    def __init__(self):
        pass
    
    def check_position(self, position: list[float]) -> bool:


        if not isinstance(position, (list)) or len(position) != 3:
            print("[WARN]: Position muss eine Listemit 3 Elementen sein.")
            return False
        
       
        if not (X_MIN <= position[0] <= X_MAX):
            print(f"[WARN]: X-Koordinate {position[0]:.2f} außerhalb Bereich [{X_MIN}, {X_MAX}].")
            return False
        
       
        if not (Y_MIN <= position[1] <= Y_MAX):
            print(f"[WARN]: Y-Koordinate {position[1]:.2f} außerhalb Bereich [{Y_MIN}, {Y_MAX}].")
            return False
        
        print("[INFO]: Position ist plausibel.")
        return True
    
    
