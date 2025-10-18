from typing import TYPE_CHECKING

from cogip.tools.planner.actions.action_align import AlignBottomAction
from cogip.tools.planner.actions.strategy import Strategy

if TYPE_CHECKING:
    from ..planner import Planner


class TestAlignBottomStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(AlignBottomAction(planner, self))
