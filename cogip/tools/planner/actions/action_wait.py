import asyncio
from typing import TYPE_CHECKING

from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy

if TYPE_CHECKING:
    from ..planner import Planner


class WaitAction(Action):
    """
    Action used if no other action is available.
    Reset recycled attribute of all actions at the end.
    """

    def __init__(self, planner: "Planner", strategy: "Strategy", delay_seconds: int = 2):
        super().__init__("Wait action", planner, strategy)
        self.delay_seconds = delay_seconds
        self.before_action_func = self.before_wait
        self.after_action_func = self.after_wait

    def weight(self) -> float:
        return 1

    async def before_wait(self):
        self.logger.debug(f"Robot {self.planner.robot_id}: WaitAction: before action")

    async def after_wait(self):
        self.logger.debug(f"Robot {self.planner.robot_id}: WaitAction: after action")
        await asyncio.sleep(self.delay_seconds)

        for action in self.strategy:
            action.recycled = False

        self.strategy.append(WaitAction(self.planner, self.strategy, self.delay_seconds))
