class EdgeDetectorRise:
    def __init__(self):
        self.prev = False

    def update(self, current):
        rising = not self.prev and current

        self.prev = current
        return rising 
    
class EdgeDetectorFall:
    def __init__(self):
        self.prev = False

    def update(self, current):
        falling = self.prev and not current

        self.prev = current
        return falling