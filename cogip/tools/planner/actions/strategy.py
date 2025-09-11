import copy
from typing import TYPE_CHECKING
from unittest.mock import patch

from cogip.tools.planner.actions.action import Action
from cogip.utils import mock

if TYPE_CHECKING:
    from ..planner import Planner


class Strategy(list[Action]):
    """
    List of actions.
    Just inherits from list for now.
    """

    evaluated_strategies: list["Strategy"] = []

    def __init__(self, planner: "Planner"):
        super().__init__()
        self.planner = planner
        self.evaluated_actions: list[Action] = []

    def get_next_action(self) -> Action | None:
        """
        Get a next action of the strategy.
        """
        sorted_actions = sorted(
            [action for action in self if not action.recycled and action.weight() > 0],
            key=lambda action: action.weight(),
        )

        if len(sorted_actions) == 0:
            return None

        action = sorted_actions[-1]
        self.remove(action)
        return action

    def copy(self) -> "Strategy":
        new_strategy = Strategy(self.planner)
        for action in self:
            new_strategy.append(action)
        for action in self.evaluated_actions:
            new_strategy.evaluated_actions.append(action)
        return new_strategy

    async def evaluate(self):
        if self.planner.game_context.countdown <= 0:
            return

        for index in range(len(self)):
            if self[index].__class__.__name__ in ["WaitAction", "ParkingAction"]:
                continue
            mock_planner = mock.MockPlanner(self.planner)
            strategy_copy = self.copy()

            strategy_copy.planner = mock_planner

            action = strategy_copy.pop(index)

            action.planner = None
            action.strategy = None
            action_copy = copy.deepcopy(action)
            action.planner = self.planner
            action.strategy = self
            action_copy.planner = mock_planner
            action_copy.strategy = strategy_copy

            if action_copy.weight() == 0:
                continue

            Strategy.evaluated_strategies.append(strategy_copy)

            await action_copy.evaluate()
            strategy_copy.evaluated_actions.append(action)

            await strategy_copy.evaluate()

    async def start_evaluation(self):
        with (
            patch("cogip.tools.planner.actuators.positional_motor_command", mock.async_no_op),
            patch("cogip.tools.planner.actions.action.Action.logger", mock.MockDummyClass()),
            patch("asyncio.sleep", mock.MockAsyncioSleep()),
        ):
            await self.evaluate()

    def print_evaluations(self, max: int = 10):
        sorted_strategies = sorted(
            Strategy.evaluated_strategies,
            key=lambda s: (-s.planner.game_context.score, -s.planner.game_context.countdown),
        )

        print("Evaluated strategies: ", len(Strategy.evaluated_strategies))
        print("Best strategies:")
        for n, strategy in enumerate(sorted_strategies[:max]):
            print(
                f"{n + 1:>2}. "
                f"Score: {strategy.planner.game_context.score:> 3} - "
                f"Countdown: {int(strategy.planner.game_context.countdown):>-3} - "
                f"Actions: {', '.join([action.name for action in strategy.evaluated_actions])}"
            )
