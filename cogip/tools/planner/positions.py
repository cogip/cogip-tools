from enum import IntEnum, auto


class StartPosition(IntEnum):
    """
    Enum for available start positions.
    """

    Bottom = auto()
    Top = auto()
    Opposite = auto()
    PAMI2 = auto()
    PAMI3 = auto()
    PAMI4 = auto()
    PAMI5 = auto()
    Center = auto()
