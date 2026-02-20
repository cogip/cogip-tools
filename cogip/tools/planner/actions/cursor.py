import asyncio
import functools
from typing import TYPE_CHECKING

from cogip.cpp.libraries.models import MotionDirection
from cogip.models.artifacts import CollectionAreaID
from cogip.tools.planner import actuators
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.action_align import AlignTopCornerAction
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.camp import Camp
from cogip.tools.planner.pose import AdaptedPose

if TYPE_CHECKING:
    from ..planner import Planner


class CursorAction(Action):
    """
    Action used to move the cursor.
    """

    def __init__(self, planner: "Planner", strategy: Strategy, weight: float = 2000000.0, unit_test: bool = True):
        super().__init__("Cursor", planner, strategy)
        self.custom_weight = weight
        self.unit_test = unit_test
        self.before_action_func = self.before_action
        self.x = -807
        self.y_start = -1500 + 250 + 60 - 80
        self.y_end = -1500 + 700 + 60 - 80

    async def before_action(self):
        self.logger.info(f"{self.name}: before_action")
        self.poses.clear()

        if self.unit_test:
            self.planner.game_context.collection_areas[CollectionAreaID.LocalBottom].enabled = False
            self.planner.game_context.collection_areas[CollectionAreaID.LocalBottomSide].enabled = False

        if not self.planner.game_context.front_free:
            self.orientation = 90
            self.direction = MotionDirection.FORWARD_ONLY
            if Camp().color == Camp.Colors.blue:
                self.arm_open = functools.partial(actuators.back_arm_left_open, self.planner)
                self.arm_close = functools.partial(actuators.back_arm_left_close, self.planner)
                self.arms_close = functools.partial(actuators.back_arms_close, self.planner)
                self.opposite_arms_close = functools.partial(actuators.front_arms_close, self.planner)
            else:
                self.arm_open = functools.partial(actuators.back_arm_right_open, self.planner)
                self.arm_close = functools.partial(actuators.back_arm_right_close, self.planner)
                self.arms_close = functools.partial(actuators.back_arms_close, self.planner)
                self.opposite_arms_close = functools.partial(actuators.front_arms_close, self.planner)
            self.lift_up = functools.partial(actuators.back_lift_up, self.planner)
            self.lift_mid = functools.partial(actuators.back_lift_mid, self.planner)
            self.lift_down = functools.partial(actuators.back_lift_down, self.planner)
        else:
            self.orientation = -90
            self.direction = MotionDirection.BACKWARD_ONLY
            if Camp().color == Camp.Colors.blue:
                self.arm_open = functools.partial(actuators.front_arm_right_open, self.planner)
                self.arm_close = functools.partial(actuators.front_arm_right_close, self.planner)
                self.arms_close = functools.partial(actuators.front_arms_close, self.planner)
                self.opposite_arms_close = functools.partial(actuators.back_arms_close, self.planner)
            else:
                self.arm_open = functools.partial(actuators.front_arm_left_open, self.planner)
                self.arm_close = functools.partial(actuators.front_arm_left_close, self.planner)
                self.arms_close = functools.partial(actuators.front_arms_close, self.planner)
                self.opposite_arms_close = functools.partial(actuators.back_arms_close, self.planner)
            self.lift_up = functools.partial(actuators.front_lift_up, self.planner)
            self.lift_mid = functools.partial(actuators.front_lift_mid, self.planner)
            self.lift_down = functools.partial(actuators.front_lift_down, self.planner)

        # Start
        start_pose = AdaptedPose(
            x=self.x,
            y=self.y_start,
            O=self.orientation,
            max_speed_linear=30,
            max_speed_angular=30,
            motion_direction=MotionDirection.BIDIRECTIONAL,
            before_pose_func=self.before_start,
            after_pose_func=self.after_start,
        )
        self.poses.append(start_pose)
        self.logger.info(f"{self.name}: start: {start_pose.pose}")

        # End
        end_pose = AdaptedPose(
            x=self.x,
            y=self.y_end,
            O=self.orientation,
            max_speed_linear=10,
            max_speed_angular=10,
            motion_direction=self.direction,
            before_pose_func=self.before_end,
            after_pose_func=self.after_end,
        )
        self.poses.append(end_pose)
        self.logger.info(f"{self.name}: end: {end_pose.pose}")

    async def before_start(self):
        self.logger.info(f"{self.name}: before_start")
        await self.lift_up()
        await self.arms_close()
        await self.opposite_arms_close()

    async def after_start(self):
        self.logger.info(f"{self.name}: after_start")

    async def before_end(self):
        self.logger.info(f"{self.name}: before_end")
        duration_arm = await self.arm_open()
        duration_lift = await self.lift_mid()
        await asyncio.sleep(max(duration_arm, duration_lift))

    async def after_end(self):
        self.logger.info(f"{self.name}: after_end")
        duration = await self.arm_close()
        await asyncio.sleep(duration)
        await self.lift_down()

    def weight(self) -> float:
        if not self.planner.game_context.front_free and not self.planner.game_context.back_free:
            self.logger.info(f"{self.name}: Rejected: both front and back are full")
            return 0

        if not self.unit_test:
            if self.planner.game_context.collection_areas[CollectionAreaID.LocalBottom].enabled:
                self.logger.info(f"{self.name}: Rejected: local bottom collection area is not empty")
                return 0
            if self.planner.game_context.collection_areas[CollectionAreaID.LocalBottomSide].enabled:
                self.logger.info(f"{self.name}: Rejected: local bottom side collection area is not empty")
                return 0

        return self.custom_weight


class TestCursorStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(CursorAction(planner, self, 2_000_000.0, unit_test=True))


class TestAlignCursorStrategy(TestCursorStrategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.insert(0, AlignTopCornerAction(planner, self, weight=3_000_000.0))
