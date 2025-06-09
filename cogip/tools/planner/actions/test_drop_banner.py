from typing import TYPE_CHECKING

from cogip.tools.planner.actions.action_align import AlignBottomForBannerAction
from cogip.tools.planner.actions.action_drop_banner import DropBannerAction
from cogip.tools.planner.actions.actions import Actions

if TYPE_CHECKING:
    from ..planner import Planner


class TestDropBannerActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)

        self.append(AlignBottomForBannerAction(planner, self, weight=3_000_000.0))
        self.append(DropBannerAction(planner, self, 2_000_000.0))
