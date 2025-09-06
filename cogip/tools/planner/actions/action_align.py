import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from cogip import models
from cogip.tools.planner import actuators, logger
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.avoidance.avoidance import AvoidanceStrategy
from cogip.tools.planner.pose import AdaptedPose, Pose

if TYPE_CHECKING:
    from ..planner import Planner


class AlignBottomAction(Action):
    """
    Action used to align the back of the robot on the border before game start.
    Only on Bottom start position.
    """

    def __init__(
        self,
        planner: "Planner",
        strategy: Strategy,
        *,
        final_pose: models.Pose = Pose(x=-750, y=-250, O=0),
        reset_countdown=False,
        weight: float = 2000000.0,
    ):
        self.final_pose = final_pose
        self.reset_countdown = reset_countdown
        self.custom_weight = weight
        super().__init__("Align Bottom action", planner, strategy)
        self.before_action_func = self.init_poses

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def init_poses(self):
        self.avoidance_backup = AvoidanceStrategy(self.planner.shared_properties.avoidance_strategy)

        # On start, the robot is aligned on the right (blue camp) border of the Bottom start position
        self.start_pose = AdaptedPose(
            x=-750,
            y=-500 + self.planner.shared_properties.robot_width / 2,
            O=0,
        )
        await self.planner.sio_ns.emit("pose_start", self.start_pose.model_dump())

        # Align back
        pose = Pose(
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
        pose = Pose(
            x=-950 + self.planner.shared_properties.robot_length / 2,
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
            x=self.final_pose.x,
            y=self.final_pose.y,
            O=self.final_pose.O,
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
            x=-1000 + self.planner.shared_properties.robot_length / 2,
            y=self.start_pose.y,
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
            now = datetime.now(UTC)
            self.planner.countdown_start_timestamp = now
            await self.planner.sio_ns.emit(
                "start_countdown",
                (self.planner.robot_id, self.planner.game_context.game_duration, now.isoformat(), "deepskyblue"),
            )

    def weight(self) -> float:
        return self.custom_weight


class AlignBottomForBannerAction(AlignBottomAction):
    def __init__(
        self,
        planner: "Planner",
        strategy: Strategy,
        weight: float = 2000000.0,
    ):
        super().__init__(
            planner,
            strategy,
            final_pose=models.Pose(x=-1000 + 220, y=-50 - 450 / 2, O=180),
            reset_countdown=False,
            weight=weight,
        )
        self.after_action_func = self.after_action

    async def after_action(self):
        logger.info("AlignBottomForBannerAction: after_action.")
        await asyncio.gather(
            actuators.arm_left_side(self.planner),
            actuators.arm_right_side(self.planner),
            actuators.magnet_center_right_in(self.planner),
            actuators.magnet_center_left_in(self.planner),
            actuators.magnet_side_right_in(self.planner),
            actuators.magnet_side_left_in(self.planner),
            actuators.lift_125(self.planner),
        )
