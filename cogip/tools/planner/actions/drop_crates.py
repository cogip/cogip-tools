import asyncio
import functools
from typing import TYPE_CHECKING

from cogip.cpp.libraries.models import MotionDirection
from cogip.models.artifacts import Pantry, PantryID
from cogip.tools.planner import actuators
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.actions.utils import get_relative_pose
from cogip.tools.planner.pose import Pose

if TYPE_CHECKING:
    from ..planner import Planner


class DropCratesAction(Action):
    """
    Action used to drop crates on pantry.
    """

    def __init__(
        self,
        planner: "Planner",
        strategy: Strategy,
        pantry_id: PantryID,
        weight: float = 2000000.0,
    ):
        self.custom_weight = weight
        super().__init__(f"DropCrates {pantry_id.name}", planner, strategy)
        self.before_action_func = self.before_action
        self.pantry_id = pantry_id
        self.shift_drop = 140
        self.shift_approach = self.shift_drop + 150
        self.shift_step_back = self.shift_approach

    @property
    def pantry(self) -> Pantry:
        return self.planner.game_context.pantries[self.pantry_id]

    async def recycle(self):
        self.pantry.enabled = False
        self.recycled = True

    async def before_action(self):
        self.logger.info(f"{self.name}: before_action")
        self.poses.clear()

        self.pantry_enabled_backup = self.pantry.enabled

        if not self.planner.game_context.front_free:
            self.arms_open = functools.partial(actuators.front_arms_open, self.planner)
            self.lift_down = functools.partial(actuators.front_lift_down, self.planner)
            self.grips_open = functools.partial(actuators.front_grips_open, self.planner)
        else:
            self.arms_open = functools.partial(actuators.back_arms_open, self.planner)
            self.lift_down = functools.partial(actuators.back_lift_down, self.planner)
            self.grips_open = functools.partial(actuators.back_grips_open, self.planner)

        # Approach
        approach_pose = Pose(
            **get_relative_pose(
                self.pantry,
                front_offset=-self.shift_approach,
                angular_offset=0 if not self.planner.game_context.front_free else 180,
            ).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BIDIRECTIONAL,
            before_pose_func=self.before_approach,
            after_pose_func=self.after_approach,
        )
        self.poses.append(approach_pose)
        self.logger.info(f"{self.name}: approach: {approach_pose.pose}")

        # Drop
        drop_pose = Pose(
            **get_relative_pose(
                self.pantry,
                front_offset=-self.shift_drop,
                angular_offset=0 if not self.planner.game_context.front_free else 180,
            ).model_dump(),
            max_speed_linear=20,
            max_speed_angular=20,
            motion_direction=(
                MotionDirection.FORWARD_ONLY
                if not self.planner.game_context.front_free
                else MotionDirection.BACKWARD_ONLY
            ),
            bypass_final_orientation=True,
            bypass_anti_blocking=True,
            before_pose_func=self.before_drop,
            after_pose_func=self.after_drop,
        )
        self.poses.append(drop_pose)
        self.logger.info(f"{self.name}: drop: {drop_pose.pose}")

    async def before_approach(self):
        self.logger.info(f"{self.name}: before_approach")

    async def after_approach(self):
        self.logger.info(f"{self.name}: after_approach")

    async def before_drop(self):
        self.logger.info(f"{self.name}: before_drop")
        self.pantry_enabled_backup = self.pantry.enabled
        self.pantry.enabled = False
        duration = await self.grips_open()
        await asyncio.sleep(duration)
        duration = await self.lift_down()
        await asyncio.sleep(duration)
        await self.arms_open()

    async def after_drop(self):
        self.logger.info(f"{self.name}: after_drop")

        # Step back
        pose_current = self.pose_current
        step_back_pose = Pose(
            **get_relative_pose(
                pose_current,
                front_offset=-self.shift_step_back,
            ).model_dump(),
            max_speed_linear=50,
            max_speed_angular=50,
            motion_direction=(
                MotionDirection.BACKWARD_ONLY
                if not self.planner.game_context.front_free
                else MotionDirection.FORWARD_ONLY
            ),
            bypass_final_orientation=True,
            before_pose_func=self.before_step_back,
            after_pose_func=self.after_step_back,
        )
        self.poses.append(step_back_pose)
        self.logger.info(f"{self.name}: step back: {step_back_pose.pose}")

    async def before_step_back(self):
        self.logger.info(f"{self.name}: before_step_back")

    async def after_step_back(self):
        self.logger.info(f"{self.name}: after_step_back")
        self.pantry.enabled = True
        if not self.planner.game_context.front_free:
            self.planner.game_context.front_free = True
        else:
            self.planner.game_context.back_free = True

    def weight(self) -> float:
        if self.planner.game_context.front_free and self.planner.game_context.back_free:
            self.logger.info(f"{self.name}: Rejected: both front and back are free")
            return 0

        return self.custom_weight
