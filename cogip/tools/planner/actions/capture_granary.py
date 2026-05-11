import asyncio
import functools
from typing import TYPE_CHECKING

from cogip.cpp.libraries.models import MotionDirection
from cogip.tools.planner import actuators
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.action_align import AlignTopCornerAction
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.cameras import get_robot_position
from cogip.tools.planner.camp import Camp
from cogip.tools.planner.pose import AdaptedPose, Pose
from cogip.tools.planner.table import TableEnum

if TYPE_CHECKING:
    from ..planner import Planner


class CaptureGranaryAction(Action):
    """
    Action used to capture crates on the granary border.
    """

    def __init__(
        self,
        planner: "Planner",
        strategy: Strategy,
        weight: float = 2_000_000.0,
    ):
        self.custom_weight = weight
        super().__init__("CaptureGranary", planner, strategy)
        self.before_action_func = self.before_action
        self.disable_fixed_obstacles_backup: bool | None = None
        self.border_offset = 115
        self.align_granary_border_x = 1000 - 450 - self.border_offset
        self.y = -700
        # Shifts from the align pose
        self.shift_approach = 110
        self.shift_capture_front = 15
        self.shift_capture_back = 15
        self.shift_step_back = 150
        if Camp().color == Camp.Colors.blue:
            self.good_crate_id = 36
            self.bad_crate_id = 47
        else:
            self.good_crate_id = 47
            self.bad_crate_id = 36

    async def recycle(self):
        self.recycled = True
        if self.disable_fixed_obstacles_backup is not None:
            self.planner.shared_properties.disable_fixed_obstacles = self.disable_fixed_obstacles_backup
            self.disable_fixed_obstacles_backup = None

    async def init_start_pose(self):
        pass

    async def before_action(self):
        self.logger.info(f"{self.name}: before_action")
        self.poses.clear()

        # # TODO: force back, to remove
        # self.planner.game_context.front_free = False

        if self.planner.game_context.front_free:
            self.logger.info(f"{self.name}: before_action: front selected")
            self.side = "front"
            self.shift_capture = self.shift_capture_front
            self.crates_ids = self.planner.game_context.front_crates
            self.arms_open = functools.partial(actuators.front_arms_open, self.planner)
            self.arms_close = functools.partial(actuators.front_arms_close, self.planner)
            self.grips_open = functools.partial(actuators.front_grips_open, self.planner)
            self.grips_close = functools.partial(actuators.front_grips_close, self.planner)
            self.lift_granary = functools.partial(actuators.front_lift_granary, self.planner)
            self.lift_up = functools.partial(actuators.front_lift_up, self.planner)
        else:
            self.logger.info(f"{self.name}: before_action: back selected")
            self.side = "back"
            self.shift_capture = self.shift_capture_back
            self.crates_ids = self.planner.game_context.back_crates
            self.arms_open = functools.partial(actuators.back_arms_open, self.planner)
            self.arms_close = functools.partial(actuators.back_arms_close, self.planner)
            self.grips_open = functools.partial(actuators.back_grips_open, self.planner)
            self.grips_close = functools.partial(actuators.back_grips_close, self.planner)
            self.lift_granary = functools.partial(actuators.back_lift_granary, self.planner)
            self.lift_up = functools.partial(actuators.back_lift_up, self.planner)

        await self.init_start_pose()

        # Approach
        approach_pose = AdaptedPose(
            x=self.align_granary_border_x - self.shift_approach,
            y=self.y,
            O=0 if self.side == "front" else 180,
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

        # Align
        align_pose = AdaptedPose(
            x=self.align_granary_border_x + 20,
            y=self.y,
            O=0 if self.side == "front" else 180,
            max_speed_linear=5,
            max_speed_angular=5,
            motion_direction=(MotionDirection.FORWARD_ONLY if self.side == "front" else MotionDirection.BACKWARD_ONLY),
            bypass_anti_blocking=True,
            bypass_final_orientation=True,
            timeout_ms=0,
            before_pose_func=self.before_align,
            after_pose_func=self.after_align,
        )
        self.poses.append(align_pose)
        self.logger.info(f"{self.name}: align: x={align_pose.x: 5.2f} y={align_pose.y: 5.2f} O={align_pose.O: 3.2f}°")

        # Capture
        capture_pose = AdaptedPose(
            x=self.align_granary_border_x - self.shift_capture,
            y=self.y,
            O=0 if self.side == "front" else 180,
            max_speed_linear=10,
            max_speed_angular=10,
            motion_direction=(MotionDirection.BACKWARD_ONLY if self.side == "front" else MotionDirection.FORWARD_ONLY),
            bypass_final_orientation=True,
            before_pose_func=self.before_capture,
            after_pose_func=self.after_capture,
        )
        self.poses.append(capture_pose)
        self.logger.info(
            f"{self.name}: capture: x={capture_pose.x: 5.2f} y={capture_pose.y: 5.2f} O={capture_pose.O: 3.2f}°"
        )

        # Step back
        step_back_pose = AdaptedPose(
            x=self.align_granary_border_x - self.shift_step_back,
            y=self.y,
            O=0 if self.side == "front" else 180,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=(MotionDirection.BACKWARD_ONLY if self.side == "front" else MotionDirection.FORWARD_ONLY),
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
        if self.planner.game_context.front_free:
            await actuators.front_arms_close(self.planner)
            await actuators.front_lift_up(self.planner)
        if self.planner.game_context.back_free:
            await actuators.back_arms_close(self.planner)
            await actuators.back_lift_up(self.planner)

    async def after_approach(self):
        self.logger.info(f"{self.name}: after_approach")

    async def before_align(self):
        self.logger.info(f"{self.name}: before_align")
        self.disable_fixed_obstacles_backup = self.planner.shared_properties.disable_fixed_obstacles
        self.planner.shared_properties.disable_fixed_obstacles = True
        await self.lift_granary()
        await self.arms_open()
        self.logger.info(f"{self.name}: before_align end")

    async def after_align(self):
        self.logger.info(f"{self.name}: after_align")
        pose_current = self.planner.pose_current
        new_pose_current = Pose(
            x=self.align_granary_border_x,
            y=pose_current.y,
            O=0 if self.side == "front" else 180,
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            new_pose_current.x -= 1000
        self.planner.shared_pose_current_buffer.push(new_pose_current.x, new_pose_current.y, new_pose_current.O)
        await self.planner.sio_ns.emit("pose_start", new_pose_current.pose.model_dump())
        await asyncio.sleep(0.5)

    async def before_capture(self):
        self.logger.info(f"{self.name}: before_capture")

    async def after_capture(self):
        self.logger.info(f"{self.name}: after_capture")
        await self.grips_open()
        duration = await self.arms_close()
        await asyncio.sleep(duration / 2)

    async def before_step_back(self):
        self.logger.info(f"{self.name}: before_step_back")

    async def after_step_back(self):
        self.logger.info(f"{self.name}: after_step_back")
        self.planner.shared_properties.disable_fixed_obstacles = self.disable_fixed_obstacles_backup
        self.disable_fixed_obstacles_backup = None

        # Wait for the crates to stop moving
        await asyncio.sleep(0.5)

        duration = await self.lift_up()
        await asyncio.sleep(duration / 2)
        duration = await self.grips_close()
        await asyncio.sleep(duration)

        self.crates_ids[:] = [self.good_crate_id, self.good_crate_id, self.good_crate_id, self.good_crate_id]

        # # TODO: force back, to remove
        # self.planner.game_context.front_free = True

    def weight(self) -> float:
        if not self.planner.game_context.front_free and not self.planner.game_context.back_free:
            self.logger.info(f"{self.name}: Rejected: both front and back are full")
            return 0

        return self.custom_weight


class TestCaptureGranaryStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(CaptureGranaryAction(planner, self, 2_000_000.0))


class CaptureGranaryCameraAction(CaptureGranaryAction):
    async def init_start_pose(self):
        # On start, the robot is inside the Top start area, oriented toward the Aruco tag (only useful for simulation).
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
        await self.planner.sio_ns.emit("pose_start", current_pose.model_dump(mode="json"))
        await asyncio.sleep(0.5)


class TestCaptureGranaryCameraStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(CaptureGranaryCameraAction(planner, self, 2_000_000.0))


class TestAlignCaptureGranaryStrategy(TestCaptureGranaryStrategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.insert(0, AlignTopCornerAction(planner, self, weight=3_000_000.0))
