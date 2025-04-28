from enum import IntEnum, auto

from .models import Pose


class ConstructionAreaID(IntEnum):
    """
    Enum to identify construction areas.
    """

    LocalBottomSmall = auto()
    LocalBottomLarge = auto()
    OppositeBottomSmall = auto()
    OppositeCenterLarge = auto()


class ConstructionArea(Pose):
    """
    Model for construction area.
    Coordinates indicate the center of the tribune.
    """

    id: ConstructionAreaID
    length: float = 450
    width: float
    free_slots: float
    enabled: bool = True


class ConstructionAreaSmall(ConstructionArea):
    """
    Model for small construction area.
    Coordinates indicate the center of the tribune.
    """

    width: float = 150
    free_slots: int = 1


class ConstructionAreaLarge(ConstructionArea):
    """
    Model for large construction area.
    Coordinates indicate the center of the tribune.
    """

    width: float = 450
    free_slots: int = 3


# Default positions for blue camp
construction_area_positions: dict[ConstructionAreaID, Pose] = {
    ConstructionAreaID.LocalBottomSmall: Pose(x=-925, y=-725, O=180),
    ConstructionAreaID.LocalBottomLarge: Pose(x=-755, y=-275, O=180),
    ConstructionAreaID.OppositeBottomSmall: Pose(x=-925, y=1275, O=180),
    ConstructionAreaID.OppositeCenterLarge: Pose(x=-125, y=1275, O=90),
}


class TribuneID(IntEnum):
    """
    Enum to identify raw material stock.
    """

    LocalCenter = auto()
    LocalTop = auto()
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
    TribuneID.LocalCenter: Pose(x=-50, y=-400, O=0),
    TribuneID.LocalTop: Pose(x=725, y=-675, O=0),
    TribuneID.LocalTopSide: Pose(x=325, y=-1425, O=-90),
    TribuneID.LocalBottomSide: Pose(x=-600, y=-1425, O=-90),
    TribuneID.LocalBottom: Pose(x=-750, y=-725, O=180),
    TribuneID.OppositeCenter: Pose(x=-50, y=400, O=0),
    # TribuneID.OppositeTop: Pose(x=725, y=675, O=0),  # Included in a fixed obstacle
    TribuneID.OppositeTopSide: Pose(x=325, y=1425, O=90),
    TribuneID.OppositeBottomSide: Pose(x=-600, y=1425, O=90),
    TribuneID.OppositeBottom: Pose(x=-750, y=725, O=180),
}
