from enum import IntEnum

from cogip.utils.singleton import Singleton


class Camp(metaclass=Singleton):
    """
    Class representing the camp selected before the game starts.
    """

    class Colors(IntEnum):
        blue = 0
        yellow = 1

    def __init__(self, color: Colors = Colors.blue):
        self.color = color

    def adapt_y(self, dist: float) -> float:
        """
        Adapt Y distance depending on the selected camp.
        Given the current table orientation and axes,
        only Y has to be adapted when the camp changes.
        """
        return dist if self.color == Camp.Colors.blue else -dist

    def adapt_angle(self, angle: float | None) -> float | None:
        """
        Adapt an angle depending on the actual camp.
        """
        if angle is None:
            return None
        return angle if self.color == Camp.Colors.blue else -angle
