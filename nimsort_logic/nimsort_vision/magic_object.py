from dataclasses import dataclass

@dataclass
class MagicObject:
    """Class representing a detected object with its type and position."""
    object_type: int
    position: tuple[float, float, float]
    ts: float
    speed: float = 1.0  #TODO Default speed in m/s, can be updated later if needed #TODO HAS TO BE UPDATED!! Default speed would be 0.01