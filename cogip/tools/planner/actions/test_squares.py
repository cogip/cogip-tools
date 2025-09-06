from typing import TYPE_CHECKING

from cogip.tools.planner import logger
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.actions import Actions, get_relative_pose
from cogip.tools.planner.avoidance.avoidance import AvoidanceStrategy
from cogip.tools.planner.pose import Pose

if TYPE_CHECKING:
    from ..planner import Planner


class TestSquaresAction(Action):
    """
    Run in square x times.
    """

    def __init__(self, planner: "Planner", actions: Actions, *, count: int, size: int):
        super().__init__(f"TestSquares action x{count}", planner, actions)
        self.count = count
        self.size = size
        self.interruptable = False
        self.before_action_func = self.before_action

    async def before_action(self):
        logger.info(f"{self.name}: before_action")
        self.planner.shared_properties.avoidance_strategy = AvoidanceStrategy.Disabled.val
        start_pose = self.pose_current
        linear_speed = 50
        angular_speed = 50

        pose1 = Pose(
            **get_relative_pose(
                start_pose,
                front_offset=self.size,
                angular_offset=90,
            ).model_dump(),
            max_speed_linear=linear_speed,
            max_speed_angular=angular_speed,
            allow_reverse=False,
        )

        pose2 = Pose(
            **get_relative_pose(
                pose1,
                front_offset=self.size,
                angular_offset=90,
            ).model_dump(),
            max_speed_linear=linear_speed,
            max_speed_angular=angular_speed,
            allow_reverse=False,
        )

        pose3 = Pose(
            **get_relative_pose(
                pose2,
                front_offset=self.size,
                angular_offset=90,
            ).model_dump(),
            max_speed_linear=linear_speed,
            max_speed_angular=angular_speed,
            allow_reverse=False,
        )

        pose4 = Pose(
            **start_pose.model_dump(),
            max_speed_linear=linear_speed,
            max_speed_angular=angular_speed,
            allow_reverse=False,
        )

        for i in range(self.count):
            self.poses.append(pose1)
            self.poses.append(pose2)
            self.poses.append(pose3)
            self.poses.append(pose4)

    def weight(self) -> float:
        return 1000000.0


class TestSquaresActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(TestSquaresAction(planner, self, count=5, size=400))
