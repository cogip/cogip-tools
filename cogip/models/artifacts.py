from enum import IntEnum, auto

from .models import Pose, Vertex


class ConstructionAreaID(IntEnum):
    """
    Enum to identify construction areas.
    """

    LocalBottomSmall = auto()
    LocalBottomLarge1 = auto()
    LocalBottomLarge2 = auto()
    LocalBottomLarge3 = auto()
    OppositeBottomSmall = auto()
    OppositeSideLarge1 = auto()
    OppositeSideLarge2 = auto()
    OppositeSideLarge3 = auto()


class ConstructionArea(Pose):
    """
    Model for construction area.
    Coordinates indicate the center of the tribune.
    """

    id: ConstructionAreaID
    length: float
    width: float = 450
    tribune_level: int = 0
    enabled: bool = True


class ConstructionAreaSmall(ConstructionArea):
    """
    Model for small construction area.
    Coordinates indicate the center of the tribune.
    """

    length: float = 150


class ConstructionAreaLarge(ConstructionArea):
    """
    Model for large construction area.
    Coordinates indicate the center of the tribune.
    """

    length: float = 450


# Default positions for blue camp
construction_area_positions: dict[ConstructionAreaID, Pose] = {
    ConstructionAreaID.LocalBottomSmall: Pose(x=-925, y=-725, O=0),
    ConstructionAreaID.LocalBottomLarge1: Pose(x=-925, y=-265, O=0),
    ConstructionAreaID.LocalBottomLarge2: Pose(x=-775, y=-265, O=0),
    ConstructionAreaID.LocalBottomLarge3: Pose(x=-625, y=-265, O=0),
    ConstructionAreaID.OppositeBottomSmall: Pose(x=-925, y=1275, O=0),
    ConstructionAreaID.OppositeSideLarge1: Pose(x=-125, y=1425, O=-90),
    ConstructionAreaID.OppositeSideLarge2: Pose(x=-125, y=1275, O=-90),
    ConstructionAreaID.OppositeSideLarge3: Pose(x=-125, y=1155, O=-90),
}


class TribuneID(IntEnum):
    """
    Enum to identify raw material stock.
    """

    LocalCenter = auto()
    LocalTop = auto()
    LocalTopTraining = auto()
    LocalBottom = auto()
    LocalTopSide = auto()
    LocalBottomSide = auto()
    OppositeCenter = auto()
    OppositeTop = auto()
    OppositeBottom = auto()
    OppositeTopSide = auto()
    OppositeBottomSide = auto()


class Tribune(Pose):
    """
    Model for raw material stock.
    Coordinates indicate the center of the tribune.
    """

    id: TribuneID
    length: float = 400.0
    width: float = 100.0
    column_count: int = 4
    platform_count: int = 2
    levels: int = 0
    construction_area: ConstructionAreaID | None = None
    private: bool = False
    enabled: bool = True


# Default positions for blue camp
tribune_positions: dict[TribuneID, Pose] = {
    TribuneID.LocalCenter: Pose(x=-50, y=-400, O=180),
    TribuneID.LocalTop: Pose(x=725, y=-675, O=180),
    TribuneID.LocalTopTraining: Pose(x=-50, y=-1100, O=180),
    TribuneID.LocalTopSide: Pose(x=325, y=-1425, O=90),
    TribuneID.LocalBottomSide: Pose(x=-600, y=-1425, O=90),
    TribuneID.LocalBottom: Pose(x=-750, y=-725, O=0),
    TribuneID.OppositeCenter: Pose(x=-50, y=400, O=180),
    # TribuneID.OppositeTop: Pose(x=725, y=675, O=180),  # Included in a fixed obstacle
    TribuneID.OppositeTopSide: Pose(x=325, y=1425, O=-90),
    TribuneID.OppositeBottomSide: Pose(x=-600, y=1425, O=-90),
    TribuneID.OppositeBottom: Pose(x=-750, y=725, O=0),
}


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
