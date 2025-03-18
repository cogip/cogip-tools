from functools import partial
from typing import TYPE_CHECKING

from cogip.models import models
from cogip.tools.planner.actions.actions import Action, Actions
from cogip.tools.planner.pose import Pose

if TYPE_CHECKING:
    from ..planner import Planner


class LinearPositionTestAction(Action):
    """
    Action used to move the robot without table.
    First set start position on 0x0.
    Them move straight forward along 100 cm.
    Then go back to start position.
    Do it in loop.
    """

    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__("LinearPositionTest action", planner, actions)
        self.distance = 750
        self.linear_speed = 66
        self.angular_speed = 66
        self.allow_reverse = True
        self.before_action_func = self.init_start_position
        self.pose_init = models.Pose(
            x=-500,
            y=-300,
            O=-90,
            max_speed_linear=self.linear_speed,
            max_speed_angular=self.angular_speed,
            allow_reverse=self.allow_reverse,
        )
        self.pose_start = Pose(**self.pose_init.model_dump())
        self.pose_start.after_pose_func = partial(self.append_pose, self.pose_start)
        self.pose_end = self.pose_start.model_copy(update={"y": self.pose_start.y - self.distance})
        self.pose_end.after_pose_func = partial(self.append_pose, self.pose_end)
        self.poses.append(self.pose_end)
        self.poses.append(self.pose_start)

    async def init_start_position(self):
        await self.planner.set_pose_start(self.pose_init)
        self.planner.pose_reached = False
        self.planner.action = self

    async def append_pose(self, pose: Pose) -> None:
        self.poses.append(pose)

    def weight(self) -> float:
        return 1000000.0


class PidLinearPositionTestActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(LinearPositionTestAction(planner, self))


class AngularPositionTestAction(Action):
    """
    Action used to move the robot without table.
    First set start position on 0x0.
    Them rotate of 180° in the same position.
    Then go back to start position.
    Do it in loop.
    """

    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__("AngularPositionTest action", planner, actions)
        self.angular_distance = 180
        self.linear_speed = 66
        self.angular_speed = 66
        self.allow_reverse = True
        self.before_action_func = self.init_start_position
        self.pose_init = models.Pose(
            x=-500,
            y=-300,
            O=-90,
            max_speed_linear=self.linear_speed,
            max_speed_angular=self.angular_speed,
            allow_reverse=self.allow_reverse,
        )
        self.pose_start = Pose(**self.pose_init.model_dump())
        self.pose_start.after_pose_func = partial(self.append_pose, self.pose_start)
        self.pose_end = self.pose_start.model_copy(update={"O": self.pose_start.O + self.angular_distance})
        self.pose_end.after_pose_func = partial(self.append_pose, self.pose_end)
        self.poses.append(self.pose_end)
        self.poses.append(self.pose_start)

    async def init_start_position(self):
        await self.planner.set_pose_start(self.pose_init)
        self.planner.pose_reached = False
        self.planner.action = self

    async def append_pose(self, pose: Pose) -> None:
        self.poses.append(pose)

    def weight(self) -> float:
        return 1000000.0


class PidAngularPositionTestActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(AngularPositionTestAction(planner, self))
