from typing import TYPE_CHECKING

from cogip.tools.planner.actions.action_align import AlignTopCornerAction, AlignTopCornerCameraAction
from cogip.tools.planner.actions.strategy import Strategy

if TYPE_CHECKING:
    from ..planner import Planner


class TestAlignTopCornerStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(AlignTopCornerAction(planner, self))


class TestAlignTopCornerCameraStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(AlignTopCornerCameraAction(planner, self))
