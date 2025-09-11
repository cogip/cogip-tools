from typing import TYPE_CHECKING

from cogip.models.artifacts import ConstructionAreaID, TribuneID
from cogip.tools.planner.actions.action_build_tribune_x2 import BuildTribuneX2Action
from cogip.tools.planner.actions.action_capture_tribune import CaptureTribuneAction
from cogip.tools.planner.actions.strategy import Strategy

if TYPE_CHECKING:
    from ..planner import Planner


class TestTribune1x2Strategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)

        self.append(CaptureTribuneAction(planner, self, TribuneID.LocalBottom, 2_000_000.0))
        self.append(BuildTribuneX2Action(planner, self, ConstructionAreaID.LocalBottomSmall, 2_000_000.0))
