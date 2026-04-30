from typing import TYPE_CHECKING

from colorzero import Color

from cogip.cpp.libraries.models import MotionDirection
from cogip.tools.planner import actuators
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.actions.utils import set_countdown_color
from cogip.tools.planner.avoidance.avoidance import AvoidanceStrategy
from cogip.tools.planner.pose import AdaptedPose
from cogip.tools.planner.table import TableEnum

if TYPE_CHECKING:
    from ..planner import Planner


class NinjaAction(Action):
    """
    Ninja action.
    """

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = True):
        super().__init__("Ninja action", planner, strategy, interruptable=False)
        self.before_action_func = self.before_action
        self.wait = wait

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def before_action(self):
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

        self.start_pose = self.pose_current.model_copy()

        pose1 = AdaptedPose(
            x=self.start_pose.x,
            y=-700,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose1,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        pose2 = AdaptedPose(
            x=825,
            y=-700,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose2,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose2)

        pose3 = AdaptedPose(
            x=860,
            y=-700,
            O=-90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose3,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose3)

        if self.planner.shared_properties.table == TableEnum.Training:
            pose1.x -= 1000
            pose2.x -= 1000
            pose3.x -= 1000

    async def before_pose1(self):
        self.logger.info(f"{self.name}: before_pose1")
        self.planner.led.color = Color("green")
        await set_countdown_color(self.planner, "green")

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")
        await actuators.ninja_arms_side(self.planner)

    async def before_pose2(self):
        self.logger.info(f"{self.name}: before_pose2")

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2")
        await actuators.ninja_arms_close(self.planner)

    async def before_pose3(self):
        self.logger.info(f"{self.name}: before_pose3")

    async def after_pose3(self):
        self.logger.info(f"{self.name}: after_pose3")

    def weight(self) -> float:
        return 9_999_999.0


class NinjaStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(NinjaAction(planner, self))


# Standalone strategy (for testing and qualification purposes)


class NinjaStandaloneStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(NinjaAction(planner, self, wait=False))
