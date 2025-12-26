from enum import IntEnum, auto

from .models import Vertex


class FixedObstacleID(IntEnum):
    """
    Enum to identify fixed obstacles.
    """

    Ramp = auto()
    Scene = auto()
    PitArea = auto()
    PamiStartArea = auto()
    Pami5Path = auto()
    OpponentRamp = auto()
    OpponentScene = auto()
    OpponentPitArea = auto()
    Backstage = auto()


class FixedObstacle(Vertex):
    """
    Model for fixed obstacles.
    """

    id: FixedObstacleID
    length: float
    width: float
    enabled: bool = True
