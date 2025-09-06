from functools import partial
from typing import TYPE_CHECKING

from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.pose import Pose
from cogip.tools.planner.table import get_table

if TYPE_CHECKING:
    from ..planner import Planner


class BackAndForthAction(Action):
    """
    Example action that generate its poses depending of the robot's pose
    at the beginning of the action.
    The robot will go from the current position to its opposite position in loop.
    """

    def __init__(self, planner: "Planner", strategy: Strategy):
        super().__init__("BackAndForth action", planner, strategy)
        self.before_action_func = self.compute_poses

    async def compute_poses(self) -> None:
        table = get_table(self.planner.shared_properties.table)
        x = self.planner.pose_current.x
        y = table.y_min + table.y_max - self.planner.pose_current.y
        angle = -self.planner.pose_current.O
        pose1 = Pose(
            x=x,
            y=y,
            O=angle,
            max_speed_linear=66,
            max_speed_angular=66,
        )
        pose2 = Pose(x=self.planner.pose_current.x, y=self.planner.pose_current.y, O=self.planner.pose_current.O)
        pose1.after_pose_func = partial(self.append_pose, pose1)
        pose2.after_pose_func = partial(self.append_pose, pose2)
        self.poses.append(pose1)
        self.poses.append(pose2)

    async def append_pose(self, pose: Pose) -> None:
        self.poses.append(pose)

    def weight(self) -> float:
        return 1000000.0


class TestBackAndForthStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(BackAndForthAction(planner, self))
        self.append(BackAndForthAction(planner, self))
        self.append(BackAndForthAction(planner, self))
        self.append(BackAndForthAction(planner, self))
