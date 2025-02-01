from typing import TYPE_CHECKING

from cogip.tools.planner.actions.action_align import AlignBottomForBannerAction
from cogip.tools.planner.actions.actions import Actions

if TYPE_CHECKING:
    from ..planner import Planner


class TestAlignBottomForBannerActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(AlignBottomForBannerAction(planner, self))
