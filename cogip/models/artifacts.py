from enum import IntEnum, auto

from .models import Vertex


class FixedObstacleID(IntEnum):
    """
    Enum to identify fixed obstacles.
    """

    Granary = auto()
    Nest = auto()
    OppositeNest = auto()
    Table = auto()


class FixedObstacle(Vertex):
    """
    Model for fixed obstacles.
    """

    id: FixedObstacleID
    length: float
    width: float
    enabled: bool = True
