import asyncio
from typing import TYPE_CHECKING

from cogip.tools.planner import logger
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.actions import Actions

if TYPE_CHECKING:
    from ..planner import Planner


class WaitAction(Action):
    """
    Action used if no other action is available.
    Reset recycled attribute of all actions at the end.
    """

    def __init__(self, planner: "Planner", actions: "Actions", delay_seconds: int = 2):
        super().__init__("Wait action", planner, actions)
        self.delay_seconds = delay_seconds
        self.before_action_func = self.before_wait
        self.after_action_func = self.after_wait

    def weight(self) -> float:
        return 1

    async def before_wait(self):
        logger.debug(f"Robot {self.planner.robot_id}: WaitAction: before action")

    async def after_wait(self):
        logger.debug(f"Robot {self.planner.robot_id}: WaitAction: after action")
        await asyncio.sleep(self.delay_seconds)

        for action in self.actions:
            action.recycled = False

        self.actions.append(WaitAction(self.planner, self.actions, self.delay_seconds))
