import math
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, final

from cogip import models
from cogip.tools.planner.pose import Pose

if TYPE_CHECKING:
    from ..planner import Planner


class Action:
    """
    This class represents an action of the game.
    It contains a list of Pose to reach in order.
    A function can be executed before the action starts and after it ends.
    """

    def __init__(self, name: str, planner: "Planner", actions: "Actions", interruptable: bool = True):
        self.name = name
        self.planner = planner
        self.actions = actions
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
        for action in self.actions:
            action.recycled = False

    async def recycle(self):
        """
        Function called if the action is blocked and put back in the actions list
        """
        self.recycled = True

    @property
    def pose_current(self) -> models.Pose:
        return self.planner.pose_current


class Actions(list[Action]):
    """
    List of actions.
    Just inherits from list for now.
    """

    def __init__(self, planner: "Planner"):
        super().__init__()
        self.planner = planner


def get_relative_pose(
    reference_pose: models.Pose,
    *,
    front_offset: float,
    side_offset: float = 0.0,
    angular_offset: float = 0.0,
) -> models.Pose:
    """
    Get a new pose relative to the reference pose with the specified linear and angular offsets.

    Args:
        reference_pose: The reference pose.
        front_offset: The offset in the direction of the reference's front.
        side_offset: The offset in the direction of the reference's side. Positive is to the left.
        angular_offset: The angular offset in degrees.
    """
    # This function calculates a new pose relative to a reference pose.
    new_x = (
        reference_pose.x
        + front_offset * math.cos(math.radians(reference_pose.O))
        - side_offset * math.sin(math.radians(reference_pose.O))
    )
    new_y = (
        reference_pose.y
        + front_offset * math.sin(math.radians(reference_pose.O))
        + side_offset * math.cos(math.radians(reference_pose.O))
    )
    # Normalize the angle to be between 0 and 360 degrees
    new_angle = (reference_pose.O + angular_offset) % 360
    return models.Pose(x=new_x, y=new_y, O=new_angle)


async def set_countdown_color(planner: "Planner", color: "str"):
    await planner.sio_ns.emit(
        "start_countdown",
        (
            planner.robot_id,
            planner.game_context.game_duration,
            planner.countdown_start_timestamp.isoformat(),
            color,
        ),
    )
