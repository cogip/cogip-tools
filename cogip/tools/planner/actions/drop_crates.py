import asyncio
import functools
from typing import TYPE_CHECKING

from cogip.cpp.libraries.models import MotionDirection
from cogip.models.artifacts import Pantry, PantryID
from cogip.tools.planner import actuators
from cogip.tools.planner.actions import crates_utils
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
        self.after_action_func = self.after_action
        self.pantry_id = pantry_id
        self.shift_approach = 0
        self.shift_push_forward = 100
        self.shift_step_back = 90
        self.approach_orientation_threshold = 30

    @property
    def pantry(self) -> Pantry:
        return self.planner.game_context.pantries[self.pantry_id]

    async def recycle(self):
        self.pantry.enabled = False
        self.recycled = True

    async def before_action(self):
        self.logger.info(f"{self.name}: before_action: begin")
        self.poses.clear()
        self.pantry_enabled_backup = self.pantry.enabled
        self.side = "front" if not self.planner.game_context.front_free else "back"

        if self.side == "front":
            self.arms_close = functools.partial(actuators.front_arms_close, self.planner)
            self.arms_open = functools.partial(actuators.front_arms_open, self.planner)
            self.lift_up = functools.partial(actuators.front_lift_up, self.planner)
        else:
            self.arms_close = functools.partial(actuators.back_arms_close, self.planner)
            self.arms_open = functools.partial(actuators.back_arms_open, self.planner)
            self.lift_up = functools.partial(actuators.back_lift_up, self.planner)

        # Approach
        x, y = crates_utils.shift_pantry_center_from_border(self.pantry)
        approach_pose = Pose(
            x=x,
            y=y,
            max_speed_linear=100,
            max_speed_angular=100,
            # motion_direction=MotionDirection.FORWARD_ONLY if self.side == "front" else MotionDirection.BACKWARD_ONLY,
            motion_direction=MotionDirection.BIDIRECTIONAL,
            bypass_final_orientation=True,
            before_pose_func=self.before_approach,
            after_pose_func=self.after_approach,
        )
        self.poses.append(approach_pose)
        self.logger.info(f"{self.name}: approach: {approach_pose.pose}")
        self.logger.info(f"{self.name}: before_action: end")

    async def before_approach(self):
        self.logger.info(f"{self.name}: before_approach")
        self.pantry_enabled_backup = self.pantry.enabled
        self.pantry.enabled = False

    async def generate_drop_pose(self):
        drop_pose = await crates_utils.drop_crates(self.planner, self.side)
        self.before_drop_org = drop_pose.before_pose_func
        self.after_drop_org = drop_pose.after_pose_func
        drop_pose.before_pose_func = self.before_drop
        drop_pose.after_pose_func = self.after_drop
        self.poses.append(drop_pose)

    async def after_approach(self):
        self.logger.info(f"{self.name}: after_approach: begin")

        # Optimize approach orientation if robot is not well oriented to be able to go back inside the table.
        pose_current = self.pose_current

        needs_orientation_fix = False
        if "O" in self.pantry.model_fields_set and self.pantry.O is not None:
            ideal_angle = self.pantry.O if self.side == "front" else (self.pantry.O + 180) % 360
            diff = (pose_current.O - ideal_angle + 180) % 360 - 180
            if abs(diff) > self.approach_orientation_threshold:
                needs_orientation_fix = True
                target_angle = (
                    ideal_angle
                    + (self.approach_orientation_threshold if diff > 0 else -self.approach_orientation_threshold)
                ) % 360
                self.logger.info(f"{self.name}: Add optimized approach orientation pose: {target_angle}°")
                fix_orientation_pose = Pose(
                    x=pose_current.x,
                    y=pose_current.y,
                    O=target_angle,
                    max_speed_angular=50,
                    after_pose_func=self.after_fix_orientation,
                )
                self.poses.append(fix_orientation_pose)

        if not needs_orientation_fix:
            self.logger.info(f"{self.name}: No need to add optimized approach orientation pose")
            await self.generate_drop_pose()

        self.logger.info(f"{self.name}: after_approach: end")

    async def after_fix_orientation(self):
        self.logger.info(f"{self.name}: after_fix_orientation: begin")
        await self.generate_drop_pose()
        self.logger.info(f"{self.name}: after_fix_orientation: end")

    async def before_drop(self):
        self.logger.info(f"{self.name}: before_drop: begin")
        self.recyclable = False
        await self.before_drop_org()
        self.logger.info(f"{self.name}: before_drop: end")

    async def after_drop(self):
        self.logger.info(f"{self.name}: after_drop: begin")
        await self.after_drop_org()

        pose_current = self.pose_current

        # Push crates forward to be sure they are well on the pantry
        shift_push_forward = self.shift_push_forward if self.side == "front" else -self.shift_push_forward
        push_pose = Pose(
            **get_relative_pose(pose_current, front_offset=shift_push_forward).model_dump(),
            max_speed_linear=50,
            max_speed_angular=50,
            motion_direction=MotionDirection.FORWARD_ONLY if self.side == "front" else MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_push,
            after_pose_func=self.after_push,
        )
        self.poses.append(push_pose)
        self.logger.info(f"{self.name}: push: x={push_pose.x: 5.2f} y={push_pose.y: 5.2f} O={push_pose.O: 3.2f}°")

        # Step back
        shift_step_back = self.shift_step_back if self.side == "front" else -self.shift_step_back
        step_back_pose = Pose(
            **get_relative_pose(pose_current, front_offset=-shift_step_back).model_dump(),
            max_speed_linear=50,
            max_speed_angular=50,
            motion_direction=MotionDirection.BACKWARD_ONLY if self.side == "front" else MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_step_back,
            after_pose_func=self.after_step_back,
        )
        self.poses.append(step_back_pose)
        self.logger.info(
            f"{self.name}: step back: x={step_back_pose.x: 5.2f} y={step_back_pose.y: 5.2f} O={step_back_pose.O: 3.2f}°"
        )
        self.logger.info(f"{self.name}: after_drop: end")

    async def before_push(self):
        self.logger.info(f"{self.name}: before_push")

    async def after_push(self):
        self.logger.info(f"{self.name}: after_push")

        # Open arms
        duration = await self.arms_open()
        await asyncio.sleep(duration / 2)

    async def before_step_back(self):
        self.logger.info(f"{self.name}: before_step_back")

    async def after_step_back(self):
        self.logger.info(f"{self.name}: after_step_back: begin")
        # Move lift up at max speed
        duration = await self.lift_up()
        await asyncio.sleep(duration / 2)

        # Close arms
        await self.arms_close()

        self.logger.info(f"{self.name}: after_step_back: end")

    async def after_action(self):
        self.logger.info(f"{self.name}: after_action")
        self.pantry.enabled = True

    def weight(self) -> float:
        if self.planner.game_context.front_free and self.planner.game_context.back_free:
            self.logger.info(f"{self.name}: Rejected: both front and back are free")
            return 0

        if self.pantry.enabled:
            self.logger.info(f"{self.name}: Rejected: pantry already enabled")
            return 0

        if not self.planner.game_context.cursor_moved and self.pantry_id == PantryID.LocalBottom:
            self.logger.info(f"{self.name}: Rejected: cursor not moved before drop at LocalBottom pantry")
            return 0

        return self.custom_weight
