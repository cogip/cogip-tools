from typing import TYPE_CHECKING

from cogip.models.artifacts import CollectionAreaID, PantryID
from cogip.tools.planner.actions.action_align import AlignTopCornerAction
from cogip.tools.planner.actions.action_parking import ParkingAction, RunAwayAction
from cogip.tools.planner.actions.capture_crates import CaptureCratesAction
from cogip.tools.planner.actions.cursor import CursorAction
from cogip.tools.planner.actions.drop_crates import DropCratesAction
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.pose import AdaptedPose

if TYPE_CHECKING:
    from ..planner import Planner


class Game4Strategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.can_wait = True

        self.append(CursorAction(planner, self, 10_000_000.0, unit_test=False))

        self.append(CaptureCratesAction(planner, self, CollectionAreaID.LocalCenter, next(self.priority)))
        self.append(CaptureCratesAction(planner, self, CollectionAreaID.LocalBottom, next(self.priority)))

        self.append(DropCratesAction(planner, self, PantryID.MiddleBottom, next(self.priority)))
        self.append(DropCratesAction(planner, self, PantryID.MiddleCenter, next(self.priority)))

        self.append(CaptureCratesAction(planner, self, CollectionAreaID.LocalBottomSide, next(self.priority)))
        self.append(DropCratesAction(planner, self, PantryID.LocalBottom, next(self.priority)))

        self.append(CaptureCratesAction(planner, self, CollectionAreaID.LocalTopSide, next(self.priority)))
        self.append(DropCratesAction(planner, self, PantryID.LocalSide, next(self.priority)))

        self.append(RunAwayAction(planner, self))
        self.append(ParkingAction(planner, self, AdaptedPose(x=740, y=-1205, O=0).pose))


class Game4AlignStrategy(Game4Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.insert(0, AlignTopCornerAction(planner, self, weight=3_000_000.0))
