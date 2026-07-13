import asyncio
import functools
from typing import TYPE_CHECKING

from cogip.cpp.libraries.models import MotionDirection
from cogip.models.artifacts import FixedObstacleID, PantryID
from cogip.tools.planner import actuators
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.action_align import AlignTopCornerAction
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.pose import AdaptedPose
from cogip.tools.planner.table import TableEnum

if TYPE_CHECKING:
    from ..planner import Planner


class PushGranaryCratesAction(Action):
    """
    Action used to push crates pushed from the granary by the Ninja.
    """

    def __init__(
        self,
        planner: "Planner",
        strategy: Strategy,
        weight: float = 2_000_000.0,
        unit_test: bool = False,
    ):
        self.custom_weight = weight
        self.unit_test = unit_test
        super().__init__("PushGranaryCrates", planner, strategy)
        self.before_action_func = self.before_action

    async def before_action(self):
        self.logger.info(f"{self.name}: before_action")
        self.poses.clear()

        # Poses for Blue camp
        self.x = (
            1000  # Top border
            - 450  # Granary border
            - 150 / 2  # Half of the crates length
            - self.planner.shared_properties.robot_width / 2  # Half of the robot width
            + 30 / 2  # Half of the front finger
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            self.x -= 1000
        self.approach_y = -1050
        self.push_y = -460
        self.step_back_y = -600

        if self.planner.game_context.front_free:
            self.logger.info(f"{self.name}: before_action: front selected")
            self.side = "front"
            self.orientation = 90
            self.push_direction = MotionDirection.FORWARD_ONLY
            self.step_back_direction = MotionDirection.BACKWARD_ONLY
            self.lift_up = functools.partial(actuators.front_lift_up, self.planner)
        else:
            self.logger.info(f"{self.name}: before_action: back selected")
            self.side = "back"
            self.orientation = -90
            self.push_direction = MotionDirection.BACKWARD_ONLY
            self.step_back_direction = MotionDirection.FORWARD_ONLY
            self.lift_up = functools.partial(actuators.back_lift_up, self.planner)

        # Approach
        approach_pose = AdaptedPose(
            x=self.x,
            y=self.approach_y,
            O=self.orientation,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BIDIRECTIONAL,
            bypass_final_orientation=False,
            before_pose_func=self.before_approach,
            after_pose_func=self.after_approach,
        )
        self.poses.append(approach_pose)
        self.logger.info(
            f"{self.name}: approach: x={approach_pose.x: 5.2f} y={approach_pose.y: 5.2f} O={approach_pose.O: 3.2f}°"
        )

        # Push
        push_pose = AdaptedPose(
            x=self.x,
            y=self.push_y,
            O=self.orientation,
            max_speed_linear=20,
            max_speed_angular=20,
            motion_direction=self.push_direction,
            bypass_anti_blocking=True,
            bypass_final_orientation=True,
            timeout_ms=0,
            before_pose_func=self.before_push,
            after_pose_func=self.after_push,
        )
        self.poses.append(push_pose)
        self.logger.info(f"{self.name}: push: x={push_pose.x: 5.2f} y={push_pose.y: 5.2f} O={push_pose.O: 3.2f}°")

        # Step back
        step_back_pose = AdaptedPose(
            x=self.x,
            y=self.step_back_y,
            O=self.orientation,
            max_speed_linear=40,
            max_speed_angular=40,
            motion_direction=self.step_back_direction,
            bypass_final_orientation=True,
            before_pose_func=self.before_step_back,
            after_pose_func=self.after_step_back,
        )
        self.poses.append(step_back_pose)
        self.logger.info(
            f"{self.name}: step back: x={step_back_pose.x: 5.2f} y={step_back_pose.y: 5.2f} O={step_back_pose.O: 3.2f}°"
        )

    async def before_approach(self):
        self.logger.info(f"{self.name}: before_approach")
        await self.lift_up()

    async def after_approach(self):
        self.logger.info(f"{self.name}: after_approach")

    async def before_push(self):
        self.logger.info(f"{self.name}: before_push")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.CratesFromGranary].enabled = False
        await asyncio.sleep(0.2)

    async def after_push(self):
        self.logger.info(f"{self.name}: after_push")

    async def before_step_back(self):
        self.logger.info(f"{self.name}: before_step_back")

    async def after_step_back(self):
        self.logger.info(f"{self.name}: after_step_back")
        self.planner.game_context.pantries[PantryID.LocalTop].enabled = True

    def weight(self) -> float:
        if not self.planner.game_context.front_free and not self.planner.game_context.back_free:
            self.logger.info(f"{self.name}: Rejected: both front and back are full")
            return 0
        if not self.planner.game_context.crates_from_granary_available:
            self.logger.info(f"{self.name}: Rejected: no crate from granary available")
            return 0
        if self.planner.game_context.pantries[PantryID.LocalTop].enabled:
            self.logger.info(f"{self.name}: Rejected: local top pantry is enabled")
            return 0
        return self.custom_weight


class TestPushGranaryCratesStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(PushGranaryCratesAction(planner, self, 2_000_000.0, unit_test=True))


class TestAlignPushGranaryCratesStrategy(TestPushGranaryCratesStrategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.insert(0, AlignTopCornerAction(planner, self, weight=3_000_000.0))
