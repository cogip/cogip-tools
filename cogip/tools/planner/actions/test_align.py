from typing import TYPE_CHECKING

from cogip.tools.planner.actions.action_align import AlignTopCornerAction, AlignTopCornerCameraAction
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.pose import AdaptedPose
from cogip.tools.planner.table import TableEnum

if TYPE_CHECKING:
    from ..planner import Planner


class TestAlignTopCornerStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)

        final_pose = AdaptedPose(
            x=750,
            y=-1250,
            O=180,
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            final_pose.x -= 1000

        self.append(AlignTopCornerAction(planner, self, final_pose=final_pose.pose))


class TestAlignTopCornerCameraStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)

        final_pose = AdaptedPose(
            x=750,
            y=-1250,
            O=180,
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            final_pose.x -= 1000

        self.append(AlignTopCornerCameraAction(planner, self, final_pose=final_pose.pose))
