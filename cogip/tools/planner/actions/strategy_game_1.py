from typing import TYPE_CHECKING

from cogip.models import models
from cogip.models.artifacts import CollectionAreaID, PantryID
from cogip.tools.planner.actions.action_align import AlignTopCornerAction
from cogip.tools.planner.actions.action_parking import ParkingAction
from cogip.tools.planner.actions.capture_crates import CaptureCratesAction
from cogip.tools.planner.actions.cursor import CursorAction
from cogip.tools.planner.actions.drop_crates import DropCratesAction
from cogip.tools.planner.actions.steal_pantry import StealPantryAction
from cogip.tools.planner.actions.strategy import Strategy

if TYPE_CHECKING:
    from ..planner import Planner


class Game1Strategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)

        self.append(CursorAction(planner, self, 10_000_000.0, unit_test=False))

        self.append(CaptureCratesAction(planner, self, CollectionAreaID.LocalBottomSide, next(self.priority)))
        self.append(CaptureCratesAction(planner, self, CollectionAreaID.LocalBottom, next(self.priority)))
        self.append(CaptureCratesAction(planner, self, CollectionAreaID.LocalCenter, next(self.priority)))

        self.append(DropCratesAction(planner, self, PantryID.LocalSide, next(self.priority)))
        self.append(DropCratesAction(planner, self, PantryID.LocalBottom, next(self.priority)))
        self.append(DropCratesAction(planner, self, PantryID.LocalCenter, next(self.priority)))

        # self.append(StealPantryAction(planner, self, PantryID.MiddleBottom, next(self.priority)))
        # self.append(StealPantryAction(planner, self, PantryID.OppositeBottom, next(self.priority)))
        # self.append(StealPantryAction(planner, self, PantryID.OppositeCenter, next(self.priority)))

        # nest = self.planner.game_context.pantries[PantryID.Nest]
        # self.append(ParkingAction(planner, self, models.Pose(**nest.model_dump(include={"x", "y", "O"}))))


class Game1AlignStrategy(Game1Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.insert(0, AlignTopCornerAction(planner, self, weight=3_000_000.0))
