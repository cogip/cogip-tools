from typing import TYPE_CHECKING

from cogip.models.artifacts import PantryID
from cogip.tools.planner.actions.capture_crates import (
    TestAlignCaptureX1Strategy,
    TestAlignCaptureX2Strategy,
    TestCaptureX1Strategy,
    TestCaptureX2Strategy,
)
from cogip.tools.planner.actions.drop_crates import DropCratesAction

if TYPE_CHECKING:
    from ..planner import Planner


class TestCaptureDropX1Strategy(TestCaptureX1Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(DropCratesAction(planner, self, PantryID.LocalSide, 1_900_000.0))


class TestAlignCaptureDropX1Strategy(TestAlignCaptureX1Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(DropCratesAction(planner, self, PantryID.LocalSide, 1_900_000.0))


class TestCaptureDropX2Strategy(TestCaptureX2Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(DropCratesAction(planner, self, PantryID.LocalSide, 1_800_000.0))
        self.append(DropCratesAction(planner, self, PantryID.LocalBottom, 1_700_000.0))


class TestAlignCaptureDropX2Strategy(TestAlignCaptureX2Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(DropCratesAction(planner, self, PantryID.LocalSide, 1_800_000.0))
        self.append(DropCratesAction(planner, self, PantryID.LocalBottom, 1_700_000.0))
