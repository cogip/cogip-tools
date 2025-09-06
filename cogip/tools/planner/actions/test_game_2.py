from typing import TYPE_CHECKING

from cogip.models import models
from cogip.models.artifacts import ConstructionAreaID, TribuneID
from cogip.tools.planner.actions.action_build_tribune_x1 import BuildTribuneX1Action
from cogip.tools.planner.actions.action_build_tribune_x2 import BuildTribuneX2Action
from cogip.tools.planner.actions.action_build_tribune_x3 import BuildTribuneX3Action
from cogip.tools.planner.actions.action_capture_tribune import CaptureTribuneAction
from cogip.tools.planner.actions.action_drop_banner import DropBannerAction
from cogip.tools.planner.actions.action_parking import ParkingAction
from cogip.tools.planner.actions.action_wait import WaitAction
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.table import TableEnum

if TYPE_CHECKING:
    from ..planner import Planner


class Game2Strategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)

        self.append(DropBannerAction(planner, self, 3_000_000.0))

        self.append(CaptureTribuneAction(planner, self, TribuneID.LocalBottom, 2_000_000.0))
        self.append(CaptureTribuneAction(planner, self, TribuneID.LocalCenter, 1_900_000.0))
        self.append(CaptureTribuneAction(planner, self, TribuneID.LocalTop, 1_700_000.0))
        self.append(CaptureTribuneAction(planner, self, TribuneID.LocalTopSide, 1_600_000.0))
        self.append(CaptureTribuneAction(planner, self, TribuneID.LocalBottomSide, 1_500_000.0))

        self.append(BuildTribuneX1Action(planner, self, ConstructionAreaID.LocalBottomSmall, 2_000_000.0))
        self.append(BuildTribuneX1Action(planner, self, ConstructionAreaID.LocalBottomLarge1, 1_900_000.0))
        self.append(BuildTribuneX3Action(planner, self, ConstructionAreaID.LocalBottomLarge1, 1_800_000.0))
        self.append(BuildTribuneX3Action(planner, self, ConstructionAreaID.LocalBottomSmall, 1_700_000.0))
        self.append(BuildTribuneX2Action(planner, self, ConstructionAreaID.LocalBottomLarge2, 1_600_000.0))
        self.append(BuildTribuneX2Action(planner, self, ConstructionAreaID.LocalBottomLarge3, 1_500_000.0))

        self.append(BuildTribuneX1Action(planner, self, ConstructionAreaID.LocalBottomLarge2, 900_000.0))
        self.append(BuildTribuneX1Action(planner, self, ConstructionAreaID.LocalBottomLarge3, 800_000.0))
        # self.append(BuildTribuneX3Action(planner, self, ConstructionAreaID.LocalBottomLarge3, 1_400_000.0))

        self.append(WaitAction(planner, self))
        if planner.shared_properties.table == TableEnum.Training:
            self.append(ParkingAction(planner, self, models.Pose(x=-500, y=-750, O=90)))
        else:
            self.append(
                ParkingAction(
                    planner,
                    self,
                    models.Pose(x=1000 - 450, y=-900 - planner.shared_properties.robot_width / 2, O=0),
                ),
            )
