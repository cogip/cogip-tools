from enum import IntEnum, auto

from .models import Pose, Vertex


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


class CollectionAreaID(IntEnum):
    """
    Enum to identify collection areas.
    """

    LocalBottom = auto()
    LocalBottomSide = auto()
    LocalTopSide = auto()
    LocalCenter = auto()
    OppositeBottom = auto()
    OppositeBottomSide = auto()
    OppositeTopSide = auto()
    OppositeCenter = auto()


class CollectionArea(Pose):
    """
    Model for collection area.
    Coordinates indicate the center of the collection area.
    """

    id: CollectionAreaID
    length: float = 150.0
    width: float = 200.0
    enabled: bool = True
    invalid: bool = False


# Default positions for blue camp (X, Y, Angle in degrees, training)
collection_areas: dict[CollectionAreaID, tuple[float, float, float, bool]] = {
    CollectionAreaID.LocalBottom: (-825, -400, 180, True),
    CollectionAreaID.LocalBottomSide: (-600, -1325, -90, True),
    CollectionAreaID.LocalTopSide: (200, -1325, -90.0, False),
    CollectionAreaID.LocalCenter: (-200, -350, None, True),
    CollectionAreaID.OppositeBottom: (-825, 400, 180, False),
    CollectionAreaID.OppositeBottomSide: (-600, 1325, 90, False),
    CollectionAreaID.OppositeTopSide: (200, 1325, 90, False),
    CollectionAreaID.OppositeCenter: (-200, 350, None, False),
}


class PantryID(IntEnum):
    """
    Enum to identify pantries.
    """

    LocalTop = auto()
    LocalSide = auto()
    LocalBottom = auto()
    LocalCenter = auto()
    OppositeTop = auto()
    OppositeSide = auto()
    OppositeBottom = auto()
    OppositeCenter = auto()
    MiddleCenter = auto()
    MiddleBottom = auto()
    Nest = auto()


class Pantry(Pose):
    """
    Model for pantry.
    Coordinates indicate the center of the pantry.
    """

    id: PantryID
    length: float = 200.0
    width: float = 200.0
    enabled: bool = True
    invalid: bool = False


# Default positions for blue camp (X, Y, Angle in degrees, training)
pantries: dict[PantryID, tuple[float, float, float | None, bool]] = {
    PantryID.LocalTop: (450, -250, 0, False),
    PantryID.LocalSide: (-200, -1400, -90, False),
    PantryID.LocalBottom: (-900, -800, 180, True),
    PantryID.LocalCenter: (-200, -700, None, True),
    PantryID.OppositeTop: (450, 250, 0, False),
    PantryID.OppositeSide: (-200, 1400, 90, False),
    PantryID.OppositeBottom: (-900, 800, 180, False),
    PantryID.OppositeCenter: (-200, 700, None, False),
    PantryID.MiddleCenter: (-200, 0, None, False),
    PantryID.MiddleBottom: (-900, 0, 180, False),
    PantryID.Nest: (800, -1250, 0, True),
}
