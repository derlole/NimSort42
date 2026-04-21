from nimsort_motion.init_process_interface import InitProcessInterface

ZERO_ACCELERATION = (0.0, 0.0, 0.0)
HOMING_ACCELERATION = (0.004, 0.004, -0.004)

class InitProcess(InitProcessInterface):
    def __init__(self):
        self.finished = False
        self.last_x = None
        self.last_y = None
        self.last_z = None
        self.counter = 0
        self.finish_counter = 0
        self.started = False

    def start(self) -> None:
        """"start the initialization process. of the axis"""
        self.started = True

    def robot_values(self, position):
        """Set the initial values for the process. and return the corresponding acceleration commands."""
        print(f"InitProcess: Received position {position}")
        if not self.started:
            return ZERO_ACCELERATION
        
        if self.finished:
            return ZERO_ACCELERATION
        
        self.counter += 1
        x, y, z = position

        if self.last_x is None or self.last_y is None or self.last_z is None:
            self.last_x = x
            self.last_y = y
            self.last_z = z
            return HOMING_ACCELERATION
            
        dx = x - self.last_x
        dy = y - self.last_y
        dz = z - self.last_z
        self.last_x = x
        self.last_y = y
        self.last_z = z

        if self.counter < 10:
            return HOMING_ACCELERATION
        elif self.counter < 20:
            return ZERO_ACCELERATION
        else:
            if abs(dx) < 0.001 and abs(dy) < 0.001 and abs(dz) < 0.001:
                if self.finish_counter < 10:
                    self.finish_counter += 1
                else:
                    self.finished = True
            else:
                self.finish_counter = 0 
            return ZERO_ACCELERATION

    def reset(self) -> None:
        """Reset the initialization process."""
        self.last_x = None
        self.last_y = None
        self.last_z = None
        self.counter = 0

    def is_initialized(self) -> bool:
        """Check if the initialization process is complete."""
        return self.finished