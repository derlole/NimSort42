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
    
class EdgeDetectorWithTHCounter(EdgeDetectorRise):
    def __init__(self, threshold: int):
        super().__init__()
        self.counter = 0
        self.threshold = threshold

    def update(self, current):
        res_iter = False
        if self.counter >= self.threshold:
            res_iter = super().update(current)
        
        if current:
            self.counter = 0
        else:
            self.counter += 1

        return res_iter