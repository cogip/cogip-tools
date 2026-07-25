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
        pami_y = -1455
        pami_angle = 90
        pami_space_x = 5
        match position:
            case StartPositionEnum.Top:
                return AdaptedPose(
                    x=720 + training_offset_x,
                    y=-1120,
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
                    x=550 + self.shared_properties.robot_width * 0.5 + pami_space_x + training_offset_x,
                    y=pami_y,
                    O=pami_angle,
                ).pose
            case StartPositionEnum.PAMI4:
                return AdaptedPose(
                    x=550 + self.shared_properties.robot_width * 1.5 + pami_space_x * 2 + training_offset_x,
                    y=pami_y,
                    O=pami_angle,
                ).pose
            case StartPositionEnum.PAMI5:
                return AdaptedPose(
                    x=550 + self.shared_properties.robot_width * 2.5 + pami_space_x * 3 + training_offset_x,
                    y=pami_y,
                    O=pami_angle,
                ).pose
            case StartPositionEnum.PAMI6:
                return AdaptedPose(
                    x=550 + self.shared_properties.robot_width * 3.5 + pami_space_x * 4 + training_offset_x,
                    y=pami_y,
                    O=pami_angle,
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
