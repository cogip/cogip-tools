from typing import TYPE_CHECKING

from cogip.models.artifacts import ConstructionAreaID, TribuneID
from cogip.tools.planner.actions import base_actions
from cogip.tools.planner.actions.actions import Actions

if TYPE_CHECKING:
    from ..planner import Planner


class TestTribune2x3Actions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(base_actions.CaptureTribuneAction(planner, self, TribuneID.LocalBottom, 2000000.0))
        self.append(base_actions.CaptureTribuneAction(planner, self, TribuneID.LocalBottomSide, 1900000.0))
        self.append(base_actions.CaptureTribuneAction(planner, self, TribuneID.LocalCenter, 1800000.0))

        self.append(base_actions.BuildTribuneX1Action(planner, self, ConstructionAreaID.LocalBottomSmall, 2000000.0))
        self.append(base_actions.BuildTribuneX1Action(planner, self, ConstructionAreaID.LocalBottomLarge2, 1900000.0))
        self.append(base_actions.BuildTribuneX3Action(planner, self, ConstructionAreaID.LocalBottomSmall, 1800000.0))
        self.append(base_actions.BuildTribuneX3Action(planner, self, ConstructionAreaID.LocalBottomLarge2, 1700000.0))
