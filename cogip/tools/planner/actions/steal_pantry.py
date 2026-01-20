import asyncio
import functools
import math
from typing import TYPE_CHECKING

from cogip import models
from cogip.cpp.libraries.obstacles import ObstacleCircle, ObstacleRectangle
from cogip.models.artifacts import Pantry, PantryID
from cogip.models.models import MotionDirection
from cogip.tools.planner import actuators
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.action_align import AlignTopCornerAction
from cogip.tools.planner.actions.crate_analysis import CrateAnalyzer, CrateGroup
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.actions.utils import get_relative_pose
from cogip.tools.planner.cameras import get_crates_position
from cogip.tools.planner.camp import Camp
from cogip.tools.planner.pose import Pose

if TYPE_CHECKING:
    from ..planner import Planner


def shift_pantry_center_from_border(pantry: Pantry) -> tuple[float, float]:
    """
    Shift the pantry center coordinates from the border
    so its center becomes valid for avoidance.
    Only used for the inspect pose.
    """
    shift_value = 100
    x_shift_value = shift_value
    y_shift_value = Camp().adapt_y(shift_value)
    x = pantry.x
    y = pantry.y

    match pantry.id:
        case PantryID.LocalTop | PantryID.OppositeTop:
            x -= x_shift_value
        case PantryID.LocalSide:
            y += y_shift_value
        case PantryID.LocalBottom | PantryID.OppositeBottom | PantryID.MiddleBottom:
            x += x_shift_value
        case PantryID.OppositeSide:
            y -= y_shift_value

    return x, y


def transform_to_table_frame(pose_robot_frame: models.Pose, robot_pose: models.Pose) -> models.Pose:
    """
    Transform a pose from robot frame to table frame.
    """
    rad_robot = math.radians(robot_pose.O)
    cos_robot = math.cos(rad_robot)
    sin_robot = math.sin(rad_robot)

    return models.Pose(
        x=robot_pose.x + pose_robot_frame.x * cos_robot - pose_robot_frame.y * sin_robot,
        y=robot_pose.y + pose_robot_frame.x * sin_robot + pose_robot_frame.y * cos_robot,
        O=robot_pose.O + pose_robot_frame.O,
    )


class StealPantryAction(Action):
    """
    Action used to steal crates from a pantry.
    """

    def __init__(
        self,
        planner: "Planner",
        strategy: Strategy,
        pantry_id: PantryID,
        weight: float = 2000000.0,
    ):
        self.custom_weight = weight
        super().__init__(f"StealPantry {pantry_id.name}", planner, strategy)
        self.before_action_func = self.before_action
        self.pantry_id = pantry_id
        self.shift_inspect = 350
        self.shift_capture = 170
        self.shift_approach = self.shift_capture + 150
        if Camp().color == Camp.Colors.blue:
            self.good_crate_id = 36
            self.bad_crate_id = 47
        else:
            self.good_crate_id = 47
            self.bad_crate_id = 36
        self.crate_group: CrateGroup | None = None

    @property
    def pantry(self) -> Pantry:
        return self.planner.game_context.pantries[self.pantry_id]

    async def recycle(self):
        self.pantry.enabled = self.pantry_enabled_backup
        self.recycled = True

    async def before_action(self):
        self.logger.info(f"{self.name}: before_action")
        self.poses.clear()
        self.crate_group: CrateGroup | None = None
        self.pantry_enabled_backup = self.pantry.enabled
        self.pantry.enabled = False

        if self.planner.game_context.front_free:
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

        x, y = shift_pantry_center_from_border(self.pantry)
        self.inspect_pose = Pose(
            x=x,
            y=y,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BIDIRECTIONAL,
            bypass_final_orientation=False,
            stop_before_distance=self.shift_inspect,
            before_pose_func=self.before_inspect_pose,
            after_pose_func=self.after_inspect_pose,
        )
        self.poses.append(self.inspect_pose)

    async def before_inspect_pose(self):
        self.logger.info(f"{self.name}: before_inspect_pose")
        await self.arms_close()
        await self.lift_mid()

    async def after_inspect_pose(self):
        self.logger.info(f"{self.name}: after_inspect_pose")
        await asyncio.sleep(0.5)
        pose_current = self.planner.pose_current

        # Check orientation to pantry
        angle_to_pantry = math.degrees(math.atan2(self.pantry.y - pose_current.y, self.pantry.x - pose_current.x))
        angle_diff = angle_to_pantry - pose_current.O
        self.logger.info(
            f"{self.name}: angle to pantry: "
            f"{angle_to_pantry: 3.2f}°, current angle: {pose_current.O: 3.2f}°, diff: {angle_diff: 3.2f}°"
        )
        # Normalize to [-180, 180]
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360
        if abs(angle_diff) > 10:
            # Need to add an orientation adjustment pose
            self.logger.info(f"{self.name}: adding orientation adjustment pose (diff={angle_diff: 3.2f}°)")
            adjust_pose = Pose(
                x=pose_current.x,
                y=pose_current.y,
                O=angle_to_pantry,
                max_speed_linear=50,
                max_speed_angular=50,
                motion_direction=MotionDirection.BIDIRECTIONAL,
                bypass_final_orientation=False,
                before_pose_func=self.before_inspect_orientation,
                after_pose_func=self.after_inspect_orientation,
            )
            self.poses.append(adjust_pose)
        else:
            self.logger.info(f"{self.name}: orientation to pantry is acceptable (diff={angle_diff: 3.2f}°)")
            await self.after_inspect_orientation()

    async def before_inspect_orientation(self):
        self.logger.info(f"{self.name}: before_inspect_orientation")

    async def after_inspect_orientation(self):
        self.logger.info(f"{self.name}: after_inspect_orientation")
        await asyncio.sleep(0.5)
        pose_current = self.planner.pose_current
        crates_found: list[tuple[int, models.Pose]] = await get_crates_position(self.planner)
        self.logger.info(f"{self.name}: crates found:")
        for crate_id, pose in crates_found:
            self.logger.info(f"{self.name}: - {crate_id}: x={pose.x: 5.2f} y={pose.y: 5.2f} O={pose.O: 3.2f}°")

        # 1. Analyze crates to find valid groups
        analyzer = CrateAnalyzer(self.good_crate_id, self.bad_crate_id)
        valid_groups = analyzer.find_groups(crates_found)

        if not valid_groups:
            self.logger.warning(f"{self.name}: No valid crate group found")
            return

        for i, group in enumerate(valid_groups):
            self.logger.info(
                f"{self.name}: Group {i}: x={group.pose.x: 5.2f} y={group.pose.y: 5.2f} O={group.pose.O: 3.2f}°"
                f" IDs={group.crate_ids} BadCount={group.bad_crate_count}"
            )

        # 2. Select the best group that is reachable
        best_approach_pose: models.Pose | None = None

        for group in valid_groups:
            # Convert group_pose to table frame
            group_pose_table = transform_to_table_frame(group.pose, pose_current)

            self.logger.info(
                f"{self.name}: Testing group (table frame): "
                f"x={group_pose_table.x: 5.2f} y={group_pose_table.y: 5.2f} O={group_pose_table.O: 3.2f}°"
            )

            # Exclude groups too far from pantry
            dist_to_pantry = math.hypot(
                group_pose_table.x - self.pantry.x,
                group_pose_table.y - self.pantry.y,
            )
            if dist_to_pantry > 180:
                self.logger.info(f"{self.name}: Group too far from pantry (dist={dist_to_pantry:.0f}mm), skipping")
                continue

            # Update pantry state using crate group pose
            self.pantry.x = group_pose_table.x
            self.pantry.y = group_pose_table.y
            self.pantry.O = group_pose_table.O
            self.pantry.enabled = True

            # Compute possible approach positions
            front_approach_pose = get_relative_pose(
                group_pose_table,
                front_offset=-self.shift_approach,
                angular_offset=0,
            )
            back_approach_pose = get_relative_pose(
                group_pose_table,
                front_offset=self.shift_approach,
                angular_offset=180,
            )

            # Identify obstacle crates (transform to table frame)
            # A crate is part of the group if it is within 150mm of the group center (in robot frame)
            obstacle_crates_table: list[models.Pose] = []
            for _, crate_pose in crates_found:
                if crate_pose in group.crates:
                    continue
                obstacle_crates_table.append(transform_to_table_frame(crate_pose, pose_current))

            # Check reachability
            approach_pose = self.choose_approach_position(
                pose_current,
                front_approach_pose,
                back_approach_pose,
                group_pose_table,
                obstacle_crates_table,
            )

            if approach_pose:
                self.crate_group = group
                best_approach_pose = approach_pose
                self.logger.info(f"{self.name}: Found reachable group with approach: {approach_pose}")
                break
            else:
                self.logger.info(f"{self.name}: Group not reachable")

        if not self.crate_group:
            self.logger.warning(f"{self.name}: No reachable group found")
            return

        if self.crate_group.bad_crate_count == 0:
            self.logger.warning(f"{self.name}: Selected group has no bad crates, aborting steal")
            return

        # Create approach pose
        approach_pose = Pose(
            **best_approach_pose.model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BIDIRECTIONAL,
            bypass_final_orientation=True,
            before_pose_func=self.before_approach,
            after_pose_func=self.after_approach,
        )
        self.poses.append(approach_pose)
        self.logger.info(
            f"{self.name}: approach: x={approach_pose.x: 5.2f} y={approach_pose.y: 5.2f} O={approach_pose.O: 3.2f}°"
        )

        # Capture
        capture_pose = Pose(
            **get_relative_pose(
                best_approach_pose,
                front_offset=self.shift_approach - self.shift_capture,
                angular_offset=0,
            ).model_dump(),
            max_speed_linear=20,
            max_speed_angular=20,
            motion_direction=(
                MotionDirection.FORWARD_ONLY if self.planner.game_context.front_free else MotionDirection.BACKWARD_ONLY
            ),
            bypass_final_orientation=True,
            before_pose_func=self.before_capture,
            after_pose_func=self.after_capture,
        )
        self.poses.append(capture_pose)
        self.logger.info(
            f"{self.name}: capture: x={capture_pose.x: 5.2f} y={capture_pose.y: 5.2f} O={capture_pose.O: 3.2f}°"
        )

        # Step back
        step_back_pose = Pose(
            **best_approach_pose.model_dump(),
            max_speed_linear=20,
            max_speed_angular=20,
            motion_direction=(
                MotionDirection.BACKWARD_ONLY if self.planner.game_context.front_free else MotionDirection.FORWARD_ONLY
            ),
            bypass_final_orientation=True,
            before_pose_func=self.before_step_back,
            after_pose_func=self.after_step_back,
        )
        self.poses.append(step_back_pose)
        self.logger.info(
            f"{self.name}: step back: x={step_back_pose.x: 5.2f} y={step_back_pose.y: 5.2f} O={step_back_pose.O: 3.2f}°"
        )

    def choose_approach_position(
        self,
        pose_current: models.Pose,
        front_pose: models.Pose,
        back_pose: models.Pose,
        group_pose: models.Pose,
        obstacle_crates: list[models.Pose],
    ) -> models.Pose | None:
        """
        Choose the best approach position (front or back) based on distance to current pose.
        """
        valid_poses: list[models.Pose] = [front_pose, back_pose]

        # check if approach positions are within table bounds
        robot_width = self.planner.shared_properties.robot_width
        limits = self.planner.shared_table_limits.copy()
        limits[0] += robot_width / 2  # min x
        limits[1] -= robot_width / 2  # max x
        limits[2] += robot_width / 2  # min y
        limits[3] -= robot_width / 2  # max y
        for pose in valid_poses.copy():
            if not (limits[0] <= pose.x <= limits[1] and limits[2] <= pose.y <= limits[3]):
                self.logger.warning(
                    f"{self.name}: Approach position x={pose.x: 5.2f} y={pose.y: 5.2f}° out of table bounds"
                )
                valid_poses.remove(pose)

        if not valid_poses:
            self.logger.warning(f"{self.name}: No valid approach positions within table bounds")
            return None

        # Check if approach positions is not in an obstacle
        # and if the path between approach and capture pose is clear
        self.planner.shared_obstacles_lock.start_reading()
        for pose in valid_poses.copy():
            capture_pose = get_relative_pose(
                pose,
                front_offset=self.shift_approach - self.shift_capture,
                angular_offset=0,
            )

            # Check dynamic and static obstacles from planner
            is_valid = True
            for obstacle_list in [self.planner.shared_circle_obstacles, self.planner.shared_rectangle_obstacles]:
                obstacle_list: list[ObstacleCircle | ObstacleRectangle]
                for obstacle in obstacle_list:
                    if obstacle.is_point_inside(pose.x, pose.y):
                        self.logger.warning(
                            f"{self.name}: Approach position x={pose.x: 5.2f} y={pose.y: 5.2f} in obstacle"
                        )
                        is_valid = False
                        break
                    if obstacle.is_segment_crossing(pose.x, pose.y, capture_pose.x, capture_pose.y):
                        self.logger.warning(
                            f"{self.name}: Path from approach x={pose.x: 5.2f} y={pose.y: 5.2f}° "
                            f"to capture x={capture_pose.x: 5.2f} y={capture_pose.y: 5.2f}° intersects obstacle"
                        )
                        is_valid = False
                        break
                if not is_valid:
                    valid_poses.remove(pose)
                    break

            if not is_valid:
                continue

            # Check against other crates
            for crate_pose in obstacle_crates:
                obstacle = ObstacleRectangle(crate_pose.x, crate_pose.y, crate_pose.O, 160, 60, 0)
                if obstacle.is_point_inside(pose.x, pose.y):
                    self.logger.warning(
                        f"{self.name}: Approach position x={pose.x: 5.2f} y={pose.y: 5.2f}"
                        f" inside crate at x={crate_pose.x:.0f} y={crate_pose.y:.0f}"
                    )
                    is_valid = False
                    break
                if obstacle.is_segment_crossing(pose.x, pose.y, group_pose.x, group_pose.y):
                    self.logger.warning(
                        f"{self.name}: Approach path from x={pose.x: 5.2f} y={pose.y: 5.2f}"
                        f" to x={group_pose.x: 5.2f} y={group_pose.y: 5.2f} intersects crate"
                        f" at x={crate_pose.x:.0f} y={crate_pose.y:.0f}"
                    )
                    is_valid = False
                    break

            if not is_valid:
                valid_poses.remove(pose)

        self.planner.shared_obstacles_lock.finish_reading()

        if not valid_poses:
            self.logger.warning(f"{self.name}: No valid approach positions available")
            return None

        if len(valid_poses) == 1:
            self.logger.info(f"{self.name}: Only one valid approach position available")
            return valid_poses[0]

        # Select closest approach position
        dist_front = math.hypot(front_pose.x - pose_current.x, front_pose.y - pose_current.y)
        dist_back = math.hypot(back_pose.x - pose_current.x, back_pose.y - pose_current.y)

        if dist_front <= dist_back:
            self.logger.info(f"{self.name}: Chose front approach position (distance: {dist_front: 5.2f} mm)")
            return front_pose
        else:
            self.logger.info(f"{self.name}: Chose back approach position (distance: {dist_back: 5.2f} mm)")
            return back_pose

    async def before_approach(self):
        self.logger.info(f"{self.name}: before_approach")

    async def after_approach(self):
        self.logger.info(f"{self.name}: after_approach")

    async def prepare_actuators_before_capture(self):
        self.logger.info(f"{self.name}: prepare_actuators_before_capture: begin")
        duration = await self.lift_down()
        await asyncio.sleep(duration)
        duration = await self.arms_open()
        await asyncio.sleep(duration)
        self.logger.info(f"{self.name}: prepare_actuators_before_capture: end")

    async def before_capture(self):
        self.logger.info(f"{self.name}: before_capture: begin")
        self.pantry.enabled = False
        asyncio.create_task(self.prepare_actuators_before_capture())
        self.logger.info(f"{self.name}: before_capture: end")

    async def after_capture(self):
        self.logger.info(f"{self.name}: after_capture")
        await self.grips_open()
        duration = await self.arms_close()
        await asyncio.sleep(duration)
        duration = await self.lift_up()
        await asyncio.sleep(duration)
        duration = await self.grips_close()
        await asyncio.sleep(duration)

        duration = await self.arms_open()
        await asyncio.sleep(duration)
        if self.crate_group.crate_ids[0] == self.bad_crate_id:
            await self.axis_left_side_in()
        if self.crate_group.crate_ids[1] == self.bad_crate_id:
            await self.axis_left_center_in()
        if self.crate_group.crate_ids[2] == self.bad_crate_id:
            await self.axis_right_center_in()
        if self.crate_group.crate_ids[3] == self.bad_crate_id:
            await self.axis_right_side_in()
        await asyncio.sleep(actuators.AXIS_MOVE_DURATION_SEC)
        duration = await self.arms_close()
        await asyncio.sleep(duration)

        duration = await self.grips_open()
        await asyncio.sleep(duration)
        duration = await self.lift_down()
        await asyncio.sleep(duration)
        duration = await self.arms_open()
        await asyncio.sleep(duration)
        self.logger.info(f"{self.name}: after_capture done")

    async def before_step_back(self):
        self.logger.info(f"{self.name}: before_step_back")

    async def after_step_back(self):
        self.logger.info(f"{self.name}: after_step_back")
        self.pantry.enabled = True

    def weight(self) -> float:
        if not self.planner.game_context.front_free and not self.planner.game_context.back_free:
            self.logger.info(f"{self.name}: Rejected: both front and back are full")
            return 0

        return self.custom_weight


class TestStealX1Strategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(StealPantryAction(planner, self, PantryID.MiddleBottom, 2_000_000.0))


class TestAlignStealX1Strategy(TestStealX1Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.insert(0, AlignTopCornerAction(planner, self, weight=3_000_000.0))


class TestStealX2Strategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)

        self.append(StealPantryAction(planner, self, PantryID.MiddleBottom, 2_000_000.0))
        self.append(StealPantryAction(planner, self, PantryID.OppositeCenter, 1_900_000.0))


class TestAlignStealX2Strategy(TestStealX2Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.insert(0, AlignTopCornerAction(planner, self, weight=3_000_000.0))


class TestStealX3Strategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)

        self.append(StealPantryAction(planner, self, PantryID.MiddleBottom, 2_000_000.0))
        self.append(StealPantryAction(planner, self, PantryID.OppositeBottom, 1_900_000.0))
        self.append(StealPantryAction(planner, self, PantryID.OppositeCenter, 1_800_000.0))


class TestStealAllStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(StealPantryAction(planner, self, PantryID.LocalTop, 1_900_000.0))
        self.append(StealPantryAction(planner, self, PantryID.LocalCenter, 1_850_000.0))
        self.append(StealPantryAction(planner, self, PantryID.LocalSide, 1_820_000.0))
        self.append(StealPantryAction(planner, self, PantryID.LocalBottom, 1_800_000.0))
        self.append(StealPantryAction(planner, self, PantryID.MiddleBottom, 1_700_000.0))
        self.append(StealPantryAction(planner, self, PantryID.MiddleCenter, 1_600_000.0))
        self.append(StealPantryAction(planner, self, PantryID.OppositeTop, 1_500_000.0))
        self.append(StealPantryAction(planner, self, PantryID.OppositeCenter, 1_400_000.0))
        self.append(StealPantryAction(planner, self, PantryID.OppositeBottom, 1_300_000.0))
        self.append(StealPantryAction(planner, self, PantryID.OppositeSide, 1_200_000.0))
