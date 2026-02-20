from typing import TYPE_CHECKING

from cogip.models import models
from cogip.models.artifacts import CollectionAreaID, PantryID
from cogip.tools.planner.actions.action_parking import ParkingAction
from cogip.tools.planner.actions.capture_crates import CaptureCratesAction
from cogip.tools.planner.actions.drop_crates import DropCratesAction
from cogip.tools.planner.actions.steal_pantry import StealPantryAction
from cogip.tools.planner.actions.strategy import Strategy

if TYPE_CHECKING:
    from ..planner import Planner


class Game1Strategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.planner.game_context.collection_areas[CollectionAreaID.LocalCenter].O = 180
        self.append(CaptureCratesAction(planner, self, CollectionAreaID.LocalCenter, 990_000.0))
        self.append(CaptureCratesAction(planner, self, CollectionAreaID.LocalBottom, 980_000.0))
        self.append(DropCratesAction(planner, self, PantryID.LocalSide, 970_000.0))
        self.append(DropCratesAction(planner, self, PantryID.LocalBottom, 960_000.0))

        self.append(CaptureCratesAction(planner, self, CollectionAreaID.LocalBottomSide, 890_000.0))
        self.append(CaptureCratesAction(planner, self, CollectionAreaID.LocalTopSide, 880_000.0))
        self.append(DropCratesAction(planner, self, PantryID.LocalCenter, 860_000.0))

        self.append(StealPantryAction(planner, self, PantryID.MiddleBottom, 790_000.0))
        self.append(StealPantryAction(planner, self, PantryID.OppositeBottom, 780_000.0))
        self.append(StealPantryAction(planner, self, PantryID.OppositeCenter, 770_000.0))

        nest = self.planner.game_context.pantries[PantryID.Nest]
        self.append(ParkingAction(planner, self, models.Pose(**nest.model_dump(include={"x", "y", "O"}))))
