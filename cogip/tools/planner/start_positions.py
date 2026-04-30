from enum import auto

from cogip import models
from cogip.cpp.libraries.shared_memory import SharedProperties
from cogip.utils.argenum import ArgEnum
from .pose import AdaptedPose
from .table import TableEnum


class StartPositionEnum(ArgEnum):
    """
    Enum for available start positions.
    """

    Top = auto()
    NINJA = auto()
    PAMI3 = auto()
    PAMI4 = auto()
    PAMI5 = auto()
    PAMI6 = auto()


class StartPositions:
    def __init__(self, shared_properties: SharedProperties) -> None:
        self.shared_properties = shared_properties

    def get(self, position: StartPositionEnum | int | None = None) -> models.Pose:
        if position is None:
            position = self.shared_properties.start_position
        if isinstance(position, int):
            position = StartPositionEnum(position)
        training_offset_x = -1000 if self.shared_properties.table == TableEnum.Training else 0
        match position:
            case StartPositionEnum.Top:
                return AdaptedPose(
                    x=600 + self.shared_properties.robot_length / 2 + training_offset_x,
                    y=-1100 - self.shared_properties.robot_width / 2,
                    O=180,
                ).pose
            case StartPositionEnum.NINJA:
                return AdaptedPose(
                    x=800 + self.shared_properties.robot_width / 2 + training_offset_x,
                    y=-700 - self.shared_properties.robot_length / 2,
                    O=90,
                ).pose
            case StartPositionEnum.PAMI3:
                return AdaptedPose(
                    x=550 + 100 * 0.5 + training_offset_x,
                    y=-934,
                    O=-90,
                ).pose
            case StartPositionEnum.PAMI4:
                return AdaptedPose(
                    x=550 + 100 * 1.5 + training_offset_x,
                    y=-934,
                    O=-90,
                ).pose
            case StartPositionEnum.PAMI5:
                return AdaptedPose(
                    x=550 + 100 * 2.5 + training_offset_x,
                    y=-934,
                    O=-90,
                ).pose
            case StartPositionEnum.PAMI6:
                return AdaptedPose(
                    x=550 + 100 * 3.5 + training_offset_x,
                    y=-934,
                    O=-90,
                ).pose

    @property
    def current_position(self) -> models.Pose:
        return self.get(self.shared_properties.start_position)

    def is_valid(self, position: StartPositionEnum | int) -> bool:
        if isinstance(position, int):
            position = StartPositionEnum(position)
        if self.shared_properties.robot_id == 1 and position != StartPositionEnum.Top:
            return False
        if self.shared_properties.robot_id == 2 and position != StartPositionEnum.NINJA:
            return False
        if self.shared_properties.robot_id in [3, 4, 5, 6] and position not in [
            StartPositionEnum.PAMI3,
            StartPositionEnum.PAMI4,
            StartPositionEnum.PAMI5,
            StartPositionEnum.PAMI6,
        ]:
            return False
        return True
