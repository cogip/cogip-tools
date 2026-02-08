from typing import TYPE_CHECKING

from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.actuators import (
    actuators_init,
    lift1_0,
    lift1_50,
    lift1_110,
    lift2_0,
    lift2_50,
    lift2_110,
)

if TYPE_CHECKING:
    from ..planner import Planner


class InitLiftAction(Action):
    """
    Action to initialize lifts (trigger homing sequence and register GPIOs).
    """

    def __init__(self, planner: "Planner", strategy: Strategy):
        super().__init__("Init Lifts", planner, strategy)
        self.before_action_func = self.run_init

    async def run_init(self) -> None:
        await actuators_init(self.planner)

    def weight(self) -> float:
        return 1000000.0


class InitLiftStrategy(Strategy):
    """Strategy to initialize lifts."""

    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(InitLiftAction(planner, self))


class TestLift1Action(Action):
    """
    Test action for lift 1: up/down cycles.
    """

    def __init__(self, planner: "Planner", strategy: Strategy, cycles: int = 3):
        super().__init__("Test Lift 1", planner, strategy)
        self.cycles = cycles
        self.before_action_func = self.run_lift_test

    async def run_lift_test(self) -> None:
        for i in range(self.cycles):
            # Move up
            await lift1_110(self.planner)
            await self.planner.sio_ns.emit("wait", 1.5)

            # Move to middle
            await lift1_50(self.planner)
            await self.planner.sio_ns.emit("wait", 1.0)

            # Move down
            await lift1_0(self.planner)
            await self.planner.sio_ns.emit("wait", 1.5)

    def weight(self) -> float:
        return 1000000.0


class TestLift2Action(Action):
    """
    Test action for lift 2: up/down cycles.
    """

    def __init__(self, planner: "Planner", strategy: Strategy, cycles: int = 3):
        super().__init__("Test Lift 2", planner, strategy)
        self.cycles = cycles
        self.before_action_func = self.run_lift_test

    async def run_lift_test(self) -> None:
        for i in range(self.cycles):
            # Move up
            await lift2_110(self.planner)
            await self.planner.sio_ns.emit("wait", 1.5)

            # Move to middle
            await lift2_50(self.planner)
            await self.planner.sio_ns.emit("wait", 1.0)

            # Move down
            await lift2_0(self.planner)
            await self.planner.sio_ns.emit("wait", 1.5)

    def weight(self) -> float:
        return 1000000.0


class TestLift1Strategy(Strategy):
    """Strategy to test lift 1 with multiple cycles."""

    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(TestLift1Action(planner, self, cycles=3))


class TestLift2Strategy(Strategy):
    """Strategy to test lift 2 with multiple cycles."""

    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(TestLift2Action(planner, self, cycles=3))


class TestBothLiftsStrategy(Strategy):
    """Strategy to test both lifts sequentially."""

    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(TestLift1Action(planner, self, cycles=2))
        self.append(TestLift2Action(planner, self, cycles=2))
