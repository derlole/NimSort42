from dataclasses import dataclass

@dataclass
class MagicObject:
    """Class representing a detected object with its type and position."""
    object_type: int
    position: list[float]  # [x, y, z] in meters
    ts: float