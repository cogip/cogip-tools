from typing import TYPE_CHECKING

from cogip.models import models
from cogip.models.artifacts import ConstructionAreaID, FixedObstacleID, TribuneID
from cogip.tools.planner.actions.action_align import AlignBottomAction
from cogip.tools.planner.actions.action_build_tribune_x1 import BuildTribuneX1Action
from cogip.tools.planner.actions.action_build_tribune_x2 import BuildTribuneX2Action
from cogip.tools.planner.actions.action_build_tribune_x3 import BuildTribuneX3Action
from cogip.tools.planner.actions.action_capture_tribune import CaptureTribuneAction
from cogip.tools.planner.actions.action_parking import ParkingAction
from cogip.tools.planner.actions.action_wait import WaitAction
from cogip.tools.planner.actions.actions import Actions

if TYPE_CHECKING:
    from ..planner import Planner


class TestTribune2x3Actions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)

        self.append(AlignBottomAction(planner, self, reset_countdown=True, weight=3_000_000.0))

        self.append(CaptureTribuneAction(planner, self, TribuneID.LocalBottom, 2_000_000.0))
        self.append(CaptureTribuneAction(planner, self, TribuneID.LocalCenter, 1_900_000.0))
        self.append(CaptureTribuneAction(planner, self, TribuneID.LocalBottomSide, 1_800_000.0))
        self.append(CaptureTribuneAction(planner, self, TribuneID.LocalTop, 1_700_000.0))

        self.append(BuildTribuneX1Action(planner, self, ConstructionAreaID.LocalBottomSmall, 2_000_000.0))
        self.append(BuildTribuneX1Action(planner, self, ConstructionAreaID.LocalBottomLarge1, 1_900_000.0))
        self.append(BuildTribuneX3Action(planner, self, ConstructionAreaID.LocalBottomLarge1, 1_800_000.0))
        self.append(BuildTribuneX3Action(planner, self, ConstructionAreaID.LocalBottomSmall, 1_700_000.0))
        self.append(BuildTribuneX2Action(planner, self, ConstructionAreaID.LocalBottomLarge2, 1_600_000.0))

        self.append(WaitAction(planner, self))

        parking = self.planner.game_context.fixed_obstacles[FixedObstacleID.Backstage]

        self.append(
            ParkingAction(
                planner,
                self,
                models.Pose(x=parking.x - 150, y=parking.y, O=0),
            )
        )
