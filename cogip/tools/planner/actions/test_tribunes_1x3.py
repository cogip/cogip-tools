from typing import TYPE_CHECKING

from cogip.models.artifacts import ConstructionAreaID, TribuneID
from cogip.tools.planner.actions.action_build_tribune_x1 import BuildTribuneX1Action
from cogip.tools.planner.actions.action_build_tribune_x3 import BuildTribuneX3Action
from cogip.tools.planner.actions.action_capture_tribune import CaptureTribuneAction
from cogip.tools.planner.actions.actions import Actions

if TYPE_CHECKING:
    from ..planner import Planner


class TestTribune1x3Actions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(CaptureTribuneAction(planner, self, TribuneID.LocalBottom, 2_000_000.0))
        self.append(CaptureTribuneAction(planner, self, TribuneID.LocalCenter, 1_900_000.0))

        self.append(BuildTribuneX1Action(planner, self, ConstructionAreaID.LocalBottomSmall, 2_000_000.0))
        self.append(BuildTribuneX1Action(planner, self, ConstructionAreaID.LocalBottomLarge2, 1_900_000.0))
        self.append(BuildTribuneX3Action(planner, self, ConstructionAreaID.LocalBottomSmall, 1_800_000.0))
