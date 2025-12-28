import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from cogip import models
from cogip.cpp.libraries.models import MotionDirection
from cogip.tools.planner import actuators
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.avoidance.avoidance import AvoidanceStrategy
from cogip.tools.planner.cameras import get_robot_position
from cogip.tools.planner.pose import AdaptedPose, Pose
from cogip.tools.planner.table import TableEnum

if TYPE_CHECKING:
    from ..planner import Planner


class AlignTopCornerAction(Action):
    """
    Action used to align the robot on the top corner (blue camp by default) before game start.
    """

    def __init__(
        self,
        planner: "Planner",
        strategy: Strategy,
        *,
        final_pose: models.Pose | None = None,
        reset_countdown=False,
        weight: float = 2000000.0,
    ):
        self.final_pose = final_pose
        self.reset_countdown = reset_countdown
        self.custom_weight = weight
        super().__init__("Align Top Corner action", planner, strategy)
        self.before_action_func = self.before_action
        self.after_action_func = self.after_action
        self.align_x = 700
        self.align_y = -1300

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def init_start_pose(self):
        # On start, the robot is aligned on the right (blue camp) border of the Top-Right start position
        start_pose = AdaptedPose(
            x=550 + self.planner.shared_properties.robot_length / 2,
            y=-1050 - self.planner.shared_properties.robot_width / 2,
            O=90,
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            start_pose.x -= 1000

        self.planner.shared_pose_current_buffer.push(start_pose.x, start_pose.y, start_pose.O)
        await self.planner.sio_ns.emit("pose_start", start_pose.pose.model_dump())

    async def before_action(self):
        self.logger.info(f"{self.name}: before_action")
        self.avoidance_backup = AvoidanceStrategy(self.planner.shared_properties.avoidance_strategy)
        self.set_avoidance(AvoidanceStrategy.Disabled)
        self.disable_fixed_obstacles_backup = self.planner.shared_properties.disable_fixed_obstacles
        self.planner.shared_properties.disable_fixed_obstacles = True

        await self.init_start_pose()

        # Approach side
        pose = AdaptedPose(
            x=self.align_x,
            y=self.align_y,
            O=90,
            max_speed_linear=80,
            max_speed_angular=80,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_anti_blocking=False,
            timeout_ms=0,
            bypass_final_orientation=False,
            before_pose_func=self.before_approach_side,
            after_pose_func=self.after_approach_side,
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            pose.x -= 1000
        self.poses.append(pose)

    async def before_approach_side(self):
        self.logger.info(f"{self.name}: before_approach_side")
        await actuators.front_arms_close(self.planner)
        await actuators.back_arms_close(self.planner)
        await actuators.front_lift_mid(self.planner)
        await actuators.back_lift_mid(self.planner)

    async def after_approach_side(self):
        self.logger.info(f"{self.name}: after_approach_side")

        # Align side
        pose = AdaptedPose(
            x=self.align_x,
            y=-1600,
            O=90,
            max_speed_linear=10,
            max_speed_angular=10,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_anti_blocking=True,
            timeout_ms=0,
            bypass_final_orientation=True,
            before_pose_func=self.before_align_side,
            after_pose_func=self.after_align_side,
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            pose.x -= 1000
        self.poses.append(pose)

    async def before_align_side(self):
        self.logger.info(f"{self.name}: before_align_side")

    async def after_align_side(self):
        self.logger.info(f"{self.name}: after_align_side")
        pose_current = self.planner.pose_current
        new_pose_current = AdaptedPose(
            x=pose_current.x,
            y=-1500 + self.planner.shared_properties.robot_length / 2,
            O=90,
        )
        self.planner.shared_pose_current_buffer.push(new_pose_current.x, new_pose_current.y, new_pose_current.O)
        await self.planner.sio_ns.emit("pose_start", new_pose_current.pose.model_dump())
        await asyncio.sleep(0.5)

        # Approach top
        pose = AdaptedPose(
            x=pose_current.x,
            y=self.align_y,
            O=180,
            max_speed_linear=50,
            max_speed_angular=50,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_anti_blocking=False,
            timeout_ms=0,
            bypass_final_orientation=False,
            before_pose_func=self.before_approach_top,
            after_pose_func=self.after_approach_top,
        )
        self.poses.append(pose)

    async def before_approach_top(self):
        self.logger.info(f"{self.name}: before_approach_top")

    async def after_approach_top(self):
        self.logger.info(f"{self.name}: after_approach_top")
        pose_current = self.planner.pose_current

        # Align top
        pose = Pose(
            x=1100,
            y=pose_current.y,
            O=180,
            max_speed_linear=10,
            max_speed_angular=10,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_anti_blocking=True,
            timeout_ms=0,
            bypass_final_orientation=True,
            before_pose_func=self.before_align_top,
            after_pose_func=self.after_align_top,
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            pose.x -= 1000
        self.poses.append(pose)

    async def before_align_top(self):
        self.logger.info(f"{self.name}: before_align_top")

    async def after_align_top(self):
        self.logger.info(f"{self.name}: after_align_top")
        pose_current = self.planner.pose_current
        new_pose_current = Pose(
            x=1000 - self.planner.shared_properties.robot_length / 2,
            y=pose_current.y,
            O=180,
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            new_pose_current.x -= 1000
        self.planner.shared_pose_current_buffer.push(new_pose_current.x, new_pose_current.y, new_pose_current.O)
        await self.planner.sio_ns.emit("pose_start", new_pose_current.pose.model_dump())
        await asyncio.sleep(0.5)

        # Step forward
        pose = Pose(
            x=self.align_x,
            y=pose_current.y,
            O=180,
            max_speed_linear=50,
            max_speed_angular=50,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_step_forward,
            after_pose_func=self.after_step_forward,
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            pose.x -= 1000
        self.poses.append(pose)

    async def before_step_forward(self):
        self.logger.info(f"{self.name}: before_step_forward")

    async def after_step_forward(self):
        self.logger.info(f"{self.name}: after_step_forward")
        if self.final_pose:
            # Final pose
            pose = Pose(
                x=self.final_pose.x,
                y=self.final_pose.y,
                O=self.final_pose.O,
                max_speed_linear=50,
                max_speed_angular=50,
                motion_direction=MotionDirection.BIDIRECTIONAL,
                before_pose_func=self.before_final_pose,
                after_pose_func=self.after_final_pose,
            )
            self.poses.append(pose)

    async def before_final_pose(self):
        self.logger.info(f"{self.name}: before_final_pose")

    async def after_final_pose(self):
        self.logger.info(f"{self.name}: after_final_pose")

    async def after_action(self):
        self.logger.info(f"{self.name}: after_action")
        self.set_avoidance(self.avoidance_backup)
        self.planner.shared_properties.disable_fixed_obstacles = self.disable_fixed_obstacles_backup
        if self.reset_countdown:
            now = datetime.now(UTC)
            self.planner.countdown_start_timestamp = now
            await self.planner.sio_ns.emit(
                "start_countdown",
                (self.planner.robot_id, self.planner.game_context.game_duration, now.isoformat(), "deepskyblue"),
            )

    def weight(self) -> float:
        return self.custom_weight


class AlignTopCornerCameraAction(AlignTopCornerAction):
    """
    Action used to align the robot on the top corner (blue camp by default) before game start.
    Set initial pose from camera detection.
    """

    def __init__(
        self,
        planner: "Planner",
        strategy: Strategy,
        *,
        final_pose: models.Pose | None = None,
        reset_countdown=False,
        weight: float = 2000000.0,
    ):
        super().__init__(
            planner,
            strategy,
            final_pose=final_pose,
            reset_countdown=reset_countdown,
            weight=weight,
        )
        self.name = "Align Top Corner Camera action"

    async def init_start_pose(self):
        # On start, the robot is inside the Top start area, oriented toward the Aruco tag.
        init_pose = AdaptedPose(
            x=550 + self.planner.shared_properties.robot_length / 2,
            y=-1050 - self.planner.shared_properties.robot_width / 2,
            O=110,
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            init_pose.x -= 1000

        self.logger.info(f"{self.name}: Emitting initial pose for camera detection: {init_pose.pose}")
        self.planner.shared_pose_current_buffer.push(init_pose.x, init_pose.y, init_pose.O)
        await self.planner.sio_ns.emit("pose_start", init_pose.pose.model_dump())
        await asyncio.sleep(0.5)

        current_pose = await get_robot_position(self.planner)
        if current_pose:
            self.logger.info(f"{self.name}: Camera detected pose: {current_pose}")
        else:
            self.logger.warning(f"{self.name}: No camera detection, using default start pose")
            current_pose = AdaptedPose(
                x=550 + self.planner.shared_properties.robot_length / 2,
                y=-1050 - self.planner.shared_properties.robot_width / 2,
                O=90,
            )
            if self.planner.shared_properties.table == TableEnum.Training:
                current_pose.x -= 1000
        self.planner.shared_pose_current_buffer.push(current_pose.x, current_pose.y, current_pose.O)
        await self.planner.sio_ns.emit("pose_start", current_pose.pose.model_dump())
        await asyncio.sleep(0.5)
