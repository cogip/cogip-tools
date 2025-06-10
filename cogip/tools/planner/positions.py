from enum import auto

from cogip.utils.argenum import ArgEnum


class StartPosition(ArgEnum):
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
