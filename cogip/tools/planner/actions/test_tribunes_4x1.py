from typing import TYPE_CHECKING

from cogip.models.artifacts import ConstructionAreaID, TribuneID
from cogip.tools.planner.actions.action_build_tribune_x1 import BuildTribuneX1Action
from cogip.tools.planner.actions.action_capture_tribune import CaptureTribuneAction
from cogip.tools.planner.actions.strategy import Strategy

if TYPE_CHECKING:
    from ..planner import Planner


class TestTribune4x1Strategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(CaptureTribuneAction(planner, self, TribuneID.LocalBottom, 2_000_000.0))
        self.append(CaptureTribuneAction(planner, self, TribuneID.LocalCenter, 1_900_000.0))

        self.append(BuildTribuneX1Action(planner, self, ConstructionAreaID.LocalBottomSmall, 2_000_000.0))
        self.append(BuildTribuneX1Action(planner, self, ConstructionAreaID.LocalBottomLarge1, 1_900_000.0))
        self.append(BuildTribuneX1Action(planner, self, ConstructionAreaID.LocalBottomLarge2, 1_800_000.0))
        self.append(BuildTribuneX1Action(planner, self, ConstructionAreaID.LocalBottomLarge3, 1_700_000.0))
