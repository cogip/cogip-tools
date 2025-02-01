from typing import TYPE_CHECKING

from cogip.models.artifacts import ConstructionAreaID, TribuneID
from cogip.tools.planner.actions import base_actions
from cogip.tools.planner.actions.actions import Actions

if TYPE_CHECKING:
    from ..planner import Planner


class TestTribune1x2Actions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(base_actions.CaptureTribuneAction(planner, self, TribuneID.LocalBottom, 2000000.0))

        self.append(base_actions.BuildTribuneX2Action(planner, self, ConstructionAreaID.LocalBottomSmall, 2000000.0))
