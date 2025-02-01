import asyncio
from typing import TYPE_CHECKING

from cogip import models
from cogip.tools.planner import logger
from cogip.tools.planner.actions.actions import Action, Actions
from cogip.tools.planner.avoidance.avoidance import AvoidanceStrategy
from cogip.tools.planner.camp import Camp
from cogip.tools.planner.pose import AdaptedPose

if TYPE_CHECKING:
    from ..planner import Planner


class AlignBottomAction(Action):
    """
    Action used align the back of the robot on the border before game start.
    Only on Bottom start position.
    """

    def __init__(self, planner: "Planner", actions: Actions, reset_countdown=False, weight: float = 2000000.0):
        self.reset_countdown = reset_countdown
        self.custom_weight = weight
        super().__init__("Align Bottom action", planner, actions)
        self.before_action_func = self.init_poses

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.game_context.avoidance_strategy = new_strategy
        self.planner.shared_properties["avoidance_strategy"] = new_strategy

    async def init_poses(self):
        self.avoidance_backup = self.game_context.avoidance_strategy

        # On start, the robot is aligned on the right (blue camp) border of the Bottom start position
        self.start_pose = models.Pose(
            x=-750,
            y=-500 + self.game_context.properties.robot_width / 2,
            O=0,
        )
        await self.planner.sio_ns.emit("pose_start", self.start_pose.model_dump())

        # Align back
        pose = AdaptedPose(
            x=-1200,
            y=self.start_pose.y,
            O=self.start_pose.O,
            max_speed_linear=10,
            max_speed_angular=10,
            allow_reverse=True,
            bypass_anti_blocking=True,
            timeout_ms=0,
            bypass_final_orientation=True,
            before_pose_func=self.before_align_back,
            after_pose_func=self.after_align_back,
        )
        self.poses.append(pose)

        # Step forward
        pose = AdaptedPose(
            x=-950 + self.game_context.properties.robot_length / 2,
            y=self.start_pose.y,
            O=self.start_pose.O,
            max_speed_linear=50,
            max_speed_angular=50,
            allow_reverse=False,
            bypass_final_orientation=False,
            before_pose_func=self.before_step_forward,
            after_pose_func=self.after_step_forward,
        )
        self.poses.append(pose)

        # Final pose
        pose = AdaptedPose(
            x=-750,
            y=-250,
            O=0,
            max_speed_linear=50,
            max_speed_angular=50,
            allow_reverse=True,
            before_pose_func=self.before_final_pose,
            after_pose_func=self.after_final_pose,
        )
        self.poses.append(pose)

    async def before_align_back(self):
        logger.info(f"{self.name}: before_align_back")
        self.set_avoidance(AvoidanceStrategy.Disabled)

    async def after_align_back(self):
        logger.info(f"{self.name}: after_align_back")
        current_pose = models.Pose(
            x=-1000 + self.game_context.properties.robot_length / 2,
            y=Camp().adapt_y(self.start_pose.y),
            O=0,
        )
        await self.planner.sio_ns.emit("pose_start", current_pose.model_dump())
        await asyncio.sleep(1)

    async def before_step_forward(self):
        logger.info(f"{self.name}: before_step_forward")

    async def after_step_forward(self):
        logger.info(f"{self.name}: after_step_forward")

    async def before_final_pose(self):
        logger.info(f"{self.name}: before_final_pose")

    async def after_final_pose(self):
        logger.info(f"{self.name}: after_final_pose")
        self.set_avoidance(self.avoidance_backup)
        if self.reset_countdown:
            self.game_context.countdown = self.game_context.game_duration
            await self.planner.sio_ns.emit("start_countdown", self.game_context.game_duration)

    def weight(self) -> float:
        return self.custom_weight
