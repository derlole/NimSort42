from dataclasses import dataclass

@dataclass
class MagicObject:
    """Class representing a detected object with its type and position."""
    object_type: int
    position: tuple[float, float, float]
    ts: float