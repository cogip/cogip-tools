import asyncio
import math
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, final

from cogip import models
from cogip.tools.planner import logger
from cogip.tools.planner.pose import Pose

if TYPE_CHECKING:
    from ..planner import Planner
    from .strategy import Strategy


class Action:
    """
    This class represents an action of the game.
    It contains a list of Pose to reach in order.
    A function can be executed before the action starts and after it ends.
    """

    logger = logger

    def __init__(self, name: str, planner: "Planner", strategy: "Strategy", interruptable: bool = True):
        self.name = name
        self.planner = planner
        self.strategy = strategy
        self.interruptable = interruptable
        self.poses: list[Pose] = []
        self.before_action_func: Callable[[], Awaitable[None]] | None = None
        self.after_action_func: Callable[[], Awaitable[None]] | None = None
        self.recycled: bool = False

    def weight(self) -> float:
        """
        Weight of the action.
        It can be used to choose the next action to select.
        This is the generic implementation.
        """
        raise NotImplementedError

    @final
    async def act_before_action(self):
        """
        Function executed before the action starts.
        """
        if self.before_action_func:
            await self.before_action_func()

    @final
    async def act_after_action(self):
        """
        Function executed after the action ends.
        """
        if self.after_action_func:
            await self.after_action_func()

        # Re-enable all actions after a successful action
        for action in self.strategy:
            action.recycled = False

    async def recycle(self):
        """
        Function called if the action is blocked and put back in the actions list
        """
        self.recycled = True

    @property
    def pose_current(self) -> models.Pose:
        return self.planner.pose_current

    async def evaluate(self):
        # Average robot speed in mm/s.
        # This is just an empirical value found by testing that gives a good enough
        # estimation of the time needed to perform the action.
        # This could be improved later by using target speed and acceleration.
        average_speed = 100

        await self.act_before_action()

        # Update countdown
        self.planner.game_context.countdown -= asyncio.sleep.total_sleep
        asyncio.sleep.reset()

        while len(self.poses) and self.planner.game_context.countdown > 0:
            pose = self.poses.pop(0)

            await pose.act_before_pose()
            await pose.act_after_pose()

            # Update countdown
            distance = math.dist(
                (self.planner.pose_current.x, self.planner.pose_current.y),
                (pose.x, pose.y),
            )
            self.planner.game_context.countdown -= asyncio.sleep.total_sleep + distance / average_speed
            asyncio.sleep.reset()

            # Update pose_current
            self.planner.pose_current.x = pose.x
            self.planner.pose_current.y = pose.y
            self.planner.pose_current.O = pose.O

        await self.act_after_action()

        # Update countdown
        self.planner.game_context.countdown -= asyncio.sleep.total_sleep
        asyncio.sleep.reset()

    def __str__(self) -> str:
        return f"Action[0x{id(self):x}]({self.name})"

    def __repr__(self) -> str:
        return str(self)
