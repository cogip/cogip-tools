import asyncio
import functools
import math
from typing import TYPE_CHECKING

from cogip import models
from cogip.cpp.libraries.models import MotionDirection
from cogip.models.artifacts import CollectionArea, CollectionAreaID
from cogip.tools.planner import actuators
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.action_align import AlignTopCornerAction
from cogip.tools.planner.actions.crate_analysis import CrateAnalyzer
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.actions.utils import get_relative_pose
from cogip.tools.planner.cameras import get_crates_position
from cogip.tools.planner.camp import Camp
from cogip.tools.planner.pose import Pose

if TYPE_CHECKING:
    from ..planner import Planner


class CaptureCratesAction(Action):
    """
    Action used to capture crates.
    """

    def __init__(
        self,
        planner: "Planner",
        strategy: Strategy,
        collection_area_id: CollectionAreaID,
        weight: float = 2000000.0,
    ):
        self.custom_weight = weight
        super().__init__(f"CaptureCollectionArea {collection_area_id.name}", planner, strategy)
        self.before_action_func = self.before_action
        self.collection_area_id = collection_area_id
        self.shift_align = 150
        self.shift_capture = self.shift_align + 10
        self.shift_approach = self.shift_align + 160
        if Camp().color == Camp.Colors.blue:
            self.good_crate_id = 36
            self.bad_crate_id = 47
        else:
            self.good_crate_id = 47
            self.bad_crate_id = 36

    @property
    def collection_area(self) -> CollectionArea:
        return self.planner.game_context.collection_areas[self.collection_area_id]

    async def recycle(self):
        self.collection_area.enabled = True
        self.recycled = True

    async def before_action(self):
        self.logger.info(f"{self.name}: before_action")
        self.poses.clear()
        self.crates_ids: list[int] = []

        if self.planner.game_context.front_free:
            self.logger.info(f"{self.name}: before_action: front selected")
            self.arms_open = functools.partial(actuators.front_arms_open, self.planner)
            self.arms_close = functools.partial(actuators.front_arms_close, self.planner)
            self.lift_down = functools.partial(actuators.front_lift_down, self.planner)
            self.lift_mid = functools.partial(actuators.front_lift_mid, self.planner)
            self.lift_up = functools.partial(actuators.front_lift_up, self.planner)
            self.grips_open = functools.partial(actuators.front_grips_open, self.planner)
            self.grips_close = functools.partial(actuators.front_grips_close, self.planner)
            self.axis_left_side_in = functools.partial(actuators.front_axis_left_side_in, self.planner)
            self.axis_right_side_in = functools.partial(actuators.front_axis_right_side_in, self.planner)
            self.axis_left_center_in = functools.partial(actuators.front_axis_left_center_in, self.planner)
            self.axis_right_center_in = functools.partial(actuators.front_axis_right_center_in, self.planner)
        else:
            self.logger.info(f"{self.name}: before_action: back selected")
            self.arms_open = functools.partial(actuators.back_arms_open, self.planner)
            self.arms_close = functools.partial(actuators.back_arms_close, self.planner)
            self.lift_down = functools.partial(actuators.back_lift_down, self.planner)
            self.lift_mid = functools.partial(actuators.back_lift_mid, self.planner)
            self.lift_up = functools.partial(actuators.back_lift_up, self.planner)
            self.grips_open = functools.partial(actuators.back_grips_open, self.planner)
            self.grips_close = functools.partial(actuators.back_grips_close, self.planner)
            self.axis_left_side_in = functools.partial(actuators.back_axis_left_side_in, self.planner)
            self.axis_right_side_in = functools.partial(actuators.back_axis_right_side_in, self.planner)
            self.axis_left_center_in = functools.partial(actuators.back_axis_left_center_in, self.planner)
            self.axis_right_center_in = functools.partial(actuators.back_axis_right_center_in, self.planner)

        if "O" not in self.collection_area.model_fields_set:
            # Optimize collection area orientation based on robot position
            pose_current = self.pose_current
            if pose_current.x > self.collection_area.x:
                self.collection_area.O = 180.0
            else:
                self.collection_area.O = 0.0

        # Approach
        approach_pose = Pose(
            **get_relative_pose(
                self.collection_area,
                front_offset=-self.shift_approach,
                angular_offset=0,
            ).model_dump(),
            max_speed_linear=10,
            max_speed_angular=10,
            motion_direction=MotionDirection.BIDIRECTIONAL,
            before_pose_func=self.before_approach,
            after_pose_func=self.after_approach,
        )
        self.poses.append(approach_pose)
        self.logger.info(
            f"{self.name}: approach: x={approach_pose.x: 5.2f} y={approach_pose.y: 5.2f} O={approach_pose.O: 3.2f}°"
        )

        # Align
        align_pose = Pose(
            **get_relative_pose(
                self.collection_area,
                front_offset=-self.shift_align,
                angular_offset=0,
            ).model_dump(),
            max_speed_linear=10,
            max_speed_angular=10,
            motion_direction=(
                MotionDirection.FORWARD_ONLY if self.planner.game_context.front_free else MotionDirection.BACKWARD_ONLY
            ),
            before_pose_func=self.before_align,
            after_pose_func=self.after_align,
        )
        self.poses.append(align_pose)
        self.logger.info(f"{self.name}: align: x={align_pose.x: 5.2f} y={align_pose.y: 5.2f} O={align_pose.O: 3.2f}°")

        # Capture
        capture_pose = Pose(
            **get_relative_pose(
                self.collection_area,
                front_offset=-self.shift_capture,
                angular_offset=0,
            ).model_dump(),
            max_speed_linear=10,
            max_speed_angular=10,
            motion_direction=(
                MotionDirection.BACKWARD_ONLY if self.planner.game_context.front_free else MotionDirection.FORWARD_ONLY
            ),
            bypass_final_orientation=True,
            before_pose_func=self.before_capture,
            after_pose_func=self.after_capture,
        )
        self.poses.append(capture_pose)
        self.logger.info(
            f"{self.name}: capture: x={capture_pose.x: 5.2f} y={capture_pose.y: 5.2f} O={capture_pose.O: 3.2f}°"
        )

    async def before_approach(self):
        self.logger.info(f"{self.name}: before_approach")
        await self.arms_close()
        await self.lift_mid()

    async def after_approach(self):
        self.logger.info(f"{self.name}: after_approach")
        await asyncio.sleep(0.5)
        crates_found: list[tuple[int, models.Pose]] = await get_crates_position(self.planner)
        self.logger.info(f"{self.name}: crates found:")
        for crate_id, pose in crates_found:
            self.logger.info(
                f"{self.name}: - {crate_id}: x={pose.x: 5.2f} y={pose.y: 5.2f} O={pose.O: 3.2f}°"
                f" dist={math.dist((0,0),(pose.x,pose.y)):5.2f}mm"
            )

        # Analyze crates
        analyzer = CrateAnalyzer(self.good_crate_id, self.bad_crate_id)
        valid_groups = analyzer.find_groups(crates_found)

        if not valid_groups:
            self.logger.info(f"{self.name}: Rejected: no valid crate group found")
            self.poses.clear()
            self.collection_area.invalid = True
            if len(crates_found) > 0:
                # Keep obstacle
                self.collection_area.enabled = True
            return

        # Keep closest group
        valid_groups.sort(key=lambda g: math.hypot(g.pose.x, g.pose.y))
        group = valid_groups[0]

        # Check alignment with robot (angle must be close to 0 or 180)
        # Normalize angle to [-180, 180]
        max_angle_distance = 10.0  # degrees
        angle = group.pose.O
        while angle > 180:
            angle -= 360
        while angle <= -180:
            angle += 360

        # CrateAnalyzer returns crates sorted by Y coordinate in group frame
        # We need them sorted from Left (+Y robot) to Right (-Y robot) to map to actuators

        if abs(angle) < max_angle_distance:
            # Group aligned with robot (0°)
            # Group Y+ is aligned with Robot Y+.
            # Analyzer sorts by Group Y ascending -> Robot Y ascending (Right to Left).
            # We need Left to Right -> Reverse.
            self.crates_ids = list(reversed(group.crate_ids))

        elif abs(angle) > 180 - max_angle_distance:
            # Group flipped (180°)
            # Group Y+ is aligned with Robot Y-.
            # Analyzer sorts by Group Y ascending -> Robot Y descending (Left to Right).
            # Already in correct order.
            self.crates_ids = group.crate_ids

        else:
            self.logger.warning(f"{self.name}: Rejected group: angle {group.pose.O: .2f}° not close to 0° or 180°")
            self.poses.clear()
            self.collection_area.invalid = True
            self.collection_area.enabled = True
            return

        self.logger.info(f"{self.name}: Accepted group (angle={angle:.1f}°): {self.crates_ids}")

    async def prepare_actuators_before_align(self):
        self.logger.info(f"{self.name}: prepare_actuators_before_align begin")
        duration = await self.lift_down()
        await self.arms_open()
        await asyncio.sleep(duration)
        self.logger.info(f"{self.name}: prepare_actuators_before_align end")

    async def before_align(self):
        self.logger.info(f"{self.name}: before_align")
        self.collection_area.enabled = False
        await self.prepare_actuators_before_align()
        self.logger.info(f"{self.name}: before_align end")

    async def after_align(self):
        self.logger.info(f"{self.name}: after_align")

    async def before_capture(self):
        self.logger.info(f"{self.name}: before_capture")

    async def execute_actuators_after_capture(self):
        duration = await self.arms_open()
        await asyncio.sleep(duration)
        if self.crates_ids[0] == self.bad_crate_id:
            await self.axis_right_side_in()
        if self.crates_ids[1] == self.bad_crate_id:
            await self.axis_right_center_in()
        if self.crates_ids[2] == self.bad_crate_id:
            await self.axis_left_center_in()
        if self.crates_ids[3] == self.bad_crate_id:
            await self.axis_left_side_in()
        await asyncio.sleep(actuators.AXIS_MOVE_DURATION_SEC)
        await self.arms_close()

    async def after_capture(self):
        self.logger.info(f"{self.name}: after_capture")
        await self.grips_open()
        duration = await self.arms_close()
        await asyncio.sleep(duration)
        duration = await self.lift_up()
        await asyncio.sleep(duration)
        duration = await self.grips_close()
        await asyncio.sleep(duration)
        # await self.execute_actuators_after_capture()
        if self.planner.game_context.front_free:
            self.planner.game_context.front_free = False
        else:
            self.planner.game_context.back_free = False

    def weight(self) -> float:
        if not self.collection_area.enabled:
            self.logger.info(f"{self.name}: Rejected: collection area disabled")
            return 0
        if self.collection_area.invalid:
            self.logger.info(f"{self.name}: Rejected: collection area marked as invalid")
            return 0
        if not self.planner.game_context.front_free and not self.planner.game_context.back_free:
            self.logger.info(f"{self.name}: Rejected: both front and back are full")
            return 0

        return self.custom_weight


class TestCaptureX1Strategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(CaptureCratesAction(planner, self, CollectionAreaID.LocalBottomSide, 2_000_000.0))


class TestAlignCaptureX1Strategy(TestCaptureX1Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.insert(0, AlignTopCornerAction(planner, self, weight=3_000_000.0))


class TestCaptureX2Strategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)

        # self.append(CaptureCratesAction(planner, self, CollectionAreaID.LocalBottomSide, 2_000_000.0))
        # self.append(CaptureCratesAction(planner, self, CollectionAreaID.LocalBottom, 1_900_000.0))

        self.append(CaptureCratesAction(planner, self, CollectionAreaID.LocalBottom, 2_000_000.0))
        self.append(CaptureCratesAction(planner, self, CollectionAreaID.LocalCenter, 1_900_000.0))

        # self.append(CaptureCratesAction(planner, self, CollectionAreaID.OppositeCenter, 2_000_000.0))
        # self.append(CaptureCratesAction(planner, self, CollectionAreaID.OppositeBottom, 1_900_000.0))


class TestAlignCaptureX2Strategy(TestCaptureX2Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.insert(0, AlignTopCornerAction(planner, self, weight=3_000_000.0))
