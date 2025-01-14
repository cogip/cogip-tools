from enum import IntEnum, auto

from pydantic import BaseModel

from .models import Pose, Vertex


class PlantSupplyID(IntEnum):
    """
    Enum to identify plant supplies.
    """

    CenterTop = auto()
    CenterBottom = auto()
    LocalTop = auto()
    LocalBottom = auto()
    OppositeTop = auto()
    OppositeBottom = auto()


class PlantSupply(BaseModel):
    id: PlantSupplyID
    x: float
    y: float
    radius: float
    enabled: bool = True


class PotSupplyID(IntEnum):
    """
    Enum to identify pot supplies.
    """

    LocalTop = auto()
    LocalMiddle = auto()
    LocalBottom = auto()
    OppositeTop = auto()
    OppositeMiddle = auto()
    OppositeBottom = auto()


class PotSupply(BaseModel):
    id: PotSupplyID
    x: float
    y: float
    radius: float
    angle: float
    enabled: bool = True
    count: int = 5


class DropoffZoneID(IntEnum):
    """
    Enum to identify drop-off zones.
    """

    Top = auto()
    Bottom = auto()
    Opposite = auto()


class DropoffZone(Vertex):
    id: DropoffZoneID
    free_slots: int = 3


class PlanterID(IntEnum):
    """
    Enum to identify planters.
    """

    Top = auto()
    LocalSide = auto()
    OppositeSide = auto()
    Test = auto()  # To use on the training table only


class Planter(Pose):
    id: PlanterID


class SolarPanelsID(IntEnum):
    """
    Enum to identify solar panels.
    """

    Local = auto()
    Shared = auto()


class SolarPanels(Vertex):
    id: SolarPanelsID
