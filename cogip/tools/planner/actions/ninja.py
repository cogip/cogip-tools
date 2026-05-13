import asyncio
import math
from typing import TYPE_CHECKING

from colorzero import Color

from cogip.cpp.libraries.models import MotionDirection
from cogip.models.artifacts import FixedObstacleID
from cogip.tools.planner import actuators
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.actions.utils import get_relative_pose, set_countdown_color
from cogip.tools.planner.avoidance.avoidance import AvoidanceStrategy
from cogip.tools.planner.pose import AdaptedPose, Pose
from cogip.tools.planner.table import TableEnum

if TYPE_CHECKING:
    from ..planner import Planner


# Delay (seconds) inserted after each FixedObstacle enable/disable so the
# avoidance update loop and the monitor pick up the new state before the
# next pose order is dispatched.
OBSTACLE_TOGGLE_DELAY_S = 0.2


class NinjaAction(Action):
    """
    Ninja action.
    """

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = True):
        super().__init__("Ninja action", planner, strategy, interruptable=True)
        self.before_action_func = self.before_action
        self.wait = wait

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def before_action(self):
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

        self.start_pose = self.pose_current.model_copy()

        pose1 = AdaptedPose(
            x=self.start_pose.x,
            y=-700,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose1,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        pose2 = AdaptedPose(
            x=825,
            y=-700,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose2,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose2)

        pose3 = AdaptedPose(
            x=860,
            y=-700,
            O=-90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose3,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose3)

        if self.planner.shared_properties.table == TableEnum.Training:
            pose1.x -= 1000
            pose2.x -= 1000
            pose3.x -= 1000

    async def before_pose1(self):
        self.logger.info(f"{self.name}: before_pose1")
        self.planner.led.color = Color("green")
        await set_countdown_color(self.planner, "green")

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")
        await actuators.ninja_arms_side(self.planner, speed=500)

    async def before_pose2(self):
        self.logger.info(f"{self.name}: before_pose2")

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2")
        await actuators.ninja_arms_close(self.planner, speed=0)

    async def before_pose3(self):
        self.logger.info(f"{self.name}: before_pose3")

    async def after_pose3(self):
        self.logger.info(f"{self.name}: after_pose3")

    def weight(self) -> float:
        return 9_999_999.0


class NinjaStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(NinjaAction(planner, self))


# Standalone strategy (for testing and qualification purposes)


class NinjaExposeFourAction(Action):
    """
    Smooth-arc expose four (restored): deposits at (880, -700), recul to ~750,
    deploys arms in side position, then traces a 4-waypoint progressive arc to
    (890, -400, 90°). Kept alongside NinjaDropFourAction as the alternative
    drop strategy with explicit rotation. Pose 2 (initial recul) uses the
    relative-pose mechanism to avoid parasitic rotation.
    """

    EXPOSE_FOUR_BACKWARD_MM = 130

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = False):
        super().__init__("Ninja expose four", planner, strategy, interruptable=True)
        self.before_action_func = self.before_action
        self.wait = wait
        self._pose2: AdaptedPose | None = None

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def before_action(self):
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

        pose1 = AdaptedPose(
            x=880,
            y=-700,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        # pose 2 recul ~130 mm BWD from end of pose 1, on the heading axis.
        self._pose2 = AdaptedPose(
            x=0,
            y=0,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose2,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(self._pose2)

        pose2b = AdaptedPose(
            x=825,
            y=-700,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose2b,
        )
        self.poses.append(pose2b)

        pose4a = AdaptedPose(
            x=850,
            y=-695,
            O=11,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose4a,
        )
        self.poses.append(pose4a)

        pose4b = AdaptedPose(
            x=875,
            y=-680,
            O=31,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose4b,
        )
        self.poses.append(pose4b)

        pose4c = AdaptedPose(
            x=890,
            y=-640,
            O=69,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose4c,
        )
        self.poses.append(pose4c)

        pose4d = AdaptedPose(
            x=890,
            y=-550,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose4d,
        )
        self.poses.append(pose4d)

        pose5 = AdaptedPose(
            x=890,
            y=-400,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose5,
        )
        self.poses.append(pose5)

        if self.planner.shared_properties.table == TableEnum.Training:
            for pose in self.poses:
                pose.x -= 1000

    async def before_pose2(self):
        cur = self.planner.pose_current
        rad = math.radians(cur.O)
        self._pose2.x = cur.x - self.EXPOSE_FOUR_BACKWARD_MM * math.cos(rad)
        self._pose2.y = cur.y - self.EXPOSE_FOUR_BACKWARD_MM * math.sin(rad)
        self._pose2.O = cur.O
        self.logger.info(
            f"{self.name}: before_pose2 computed target ("
            f"{self._pose2.x:.1f}, {self._pose2.y:.1f}, {self._pose2.O:.1f}) "
            f"from current ({cur.x:.1f}, {cur.y:.1f}, {cur.O:.1f})"
        )

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2")
        await actuators.ninja_arms_side(self.planner, speed=500)
        await asyncio.sleep(0.5)

    async def after_pose2b(self):
        self.logger.info(f"{self.name}: after_pose2b")

    async def after_pose4a(self):
        self.logger.info(f"{self.name}: after_pose4a")

    async def after_pose4b(self):
        self.logger.info(f"{self.name}: after_pose4b")

    async def after_pose4c(self):
        self.logger.info(f"{self.name}: after_pose4c")

    async def after_pose4d(self):
        self.logger.info(f"{self.name}: after_pose4d")

    async def after_pose5(self):
        self.logger.info(f"{self.name}: after_pose5")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    def weight(self) -> float:
        # Runs first when both NinjaExposeFourAction and NinjaDropFourAction are
        # enabled. Comment one out in NinjaStandaloneStrategy to use only one.
        return 11_000_000.0


class NinjaDropFourAction(Action):
    """
    Drop four items via a shake pattern (approach, deposit, shake left/right,
    side arms, close): mostly linear translations with arms releasing items
    along the way. Replaced the older smooth-arc NinjaExposeFourAction.
    """

    DROP_FOUR_2_RECUL_MM = 50  # pose 2: back 250 mm from pose 1
    DROP_FOUR_2b_RECUL_MM = 215  # pose 2: back 250 mm from pose 1
    DROP_FOUR_3_FORWARD_MM = 200  # pose 3: forward 190 mm from pose 2 (current)
    DROP_FOUR_4_BACKWARD_MM = 100  # pose 4: back 100 mm from pose 3 (current)
    DROP_FOUR_5_FORWARD_MM = 100  # pose 5: forward 100 mm from pose 4 (current)
    DROP_FOUR_6_NORTH_MM = 40  # pose 6: 40 mm north (raw +x) from pose 5
    DROP_FOUR_8_EAST_MM = 100  # pose 8: 120 mm east (display) from pose 7 (current)
    DROP_FOUR_9_WEST_MM = 40  # pose 9: 40 mm west (display) from pose 8 (current)
    DROP_FOUR_10_X_TARGET = 880  # pose 10: north to absolute raw x = 880

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = False):
        super().__init__("Ninja drop four", planner, strategy, interruptable=True)
        self.before_action_func = self.before_action
        self.wait = wait
        # Placeholders for poses 8, 9, 10 computed at runtime from the
        # robot's current pose (absolute directions or absolute x target
        # that the chain-relative approach can't express cleanly).
        self._pose8: Pose | None = None
        self._pose9: Pose | None = None
        self._pose10: Pose | None = None

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def before_action(self):
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

        # pose 1 anchored on NinjaDropZone center (raw 675, -700): 205 mm
        # north (front_offset → raw x = 880), aligned on the zone's Y axis,
        # facing north. Reached BIDIRECTIONAL.
        drop_zone_obstacle = self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDropZone]
        drop_zone_anchor = Pose(x=drop_zone_obstacle.x, y=drop_zone_obstacle.y, O=0)
        pose1 = AdaptedPose(
            **get_relative_pose(drop_zone_anchor, front_offset=205, side_offset=0, angular_offset=0).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BIDIRECTIONAL,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        # 2: recul 55 mm relative to pose 1 (along pose 1's heading axis).
        # arms_side fires at the start (before_pose_func) at max speed so
        # the deployment runs in parallel with the slow BWD drive.
        pose2 = Pose(
            **get_relative_pose(pose1, front_offset=-self.DROP_FOUR_2_RECUL_MM).model_dump(),
            max_speed_linear=10,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose2,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose2)

        # 2: recul 55 mm relative to pose 1 (along pose 1's heading axis).
        # arms_side fires at the start (before_pose_func) at max speed so
        # the deployment runs in parallel with the slow BWD drive.
        pose2b = Pose(
            **get_relative_pose(pose2, front_offset=-self.DROP_FOUR_2b_RECUL_MM).model_dump(),
            max_speed_linear=10,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose2b,
            after_pose_func=self.after_pose2b,
        )
        self.poses.append(pose2b)

        # 3: forward 190 mm relative to pose 2 (along pose 2's heading).
        pose3 = Pose(
            **get_relative_pose(pose2b, front_offset=self.DROP_FOUR_3_FORWARD_MM).model_dump(),
            max_speed_linear=10,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose3)

        ## 4: back 100 mm relative to pose 3.
        # pose4 = Pose(
        #    **get_relative_pose(pose3, front_offset=-self.DROP_FOUR_4_BACKWARD_MM).model_dump(),
        #    max_speed_linear=10,
        #    max_speed_angular=100,
        #    motion_direction=MotionDirection.BACKWARD_ONLY,
        #    bypass_final_orientation=True,
        #    after_pose_func=self.after_pose4,
        # )
        # self.poses.append(pose4)

        ## 5: forward 100 mm relative to pose 4.
        # pose5 = Pose(
        #    **get_relative_pose(pose4, front_offset=self.DROP_FOUR_5_FORWARD_MM).model_dump(),
        #    max_speed_linear=10,
        #    max_speed_angular=100,
        #    motion_direction=MotionDirection.FORWARD_ONLY,
        #    bypass_final_orientation=True,
        #    after_pose_func=self.after_pose5,
        # )
        # self.poses.append(pose5)

        # 6: 40 mm north of pose 5 (chain pose5, front=+40 along pose 5's
        # north heading). arms_close fires in before_pose6 so the closing
        # runs in parallel with the move.
        pose6 = Pose(
            **get_relative_pose(pose3, front_offset=self.DROP_FOUR_6_NORTH_MM).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose6,
            after_pose_func=self.after_pose6,
        )
        self.poses.append(pose6)

        # 6b: clearance/approach pose due north of pose 7 at raw x=880.
        # Same raw y as pose 7 (-545), facing north (raw 0°). Smooths the
        # diagonal transit between pose 6 (north heading) and pose 7
        # (facing east) by aligning the robot on pose 7's N-S axis first.
        pose6b = AdaptedPose(
            x=880,
            y=-545,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose6b,
        )
        self.poses.append(pose6b)

        # 7: relative to pose 6 — front=-215, side=165, angular=-90 places
        # the robot at (raw 675, -535, -90°) when pose 6 ends at the
        # theoretical (890, -700, 0°), i.e. 10 mm west of NinjaDropZone
        # centered on its N-S axis, facing east. before_pose7 re-enables
        # NinjaDropZone so the avoidance plans the path around it. Final
        # orientation is bypassed so the robot ends at the motion direction.
        pose7 = AdaptedPose(
            **get_relative_pose(pose6, front_offset=-215, side_offset=165, angular_offset=-90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose7,
            after_pose_func=self.after_pose7,
        )
        self.poses.append(pose7)

        # 8: 120 mm east (display) from the pose 7 end position, reached
        # BACKWARD. Final heading is west in display so the backward motion
        # direction is east. Target computed at runtime from pose_current.
        self._pose8 = Pose(
            x=0,
            y=0,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose8,
            after_pose_func=self.after_pose8,
        )
        self.poses.append(self._pose8)

        # 9: 40 mm west (display) from the pose 8 end position, reached
        # FORWARD. Robot ends pose 8 facing west (raw +90°), so forward
        # motion goes west. Target computed at runtime from pose_current.
        self._pose9 = Pose(
            x=0,
            y=0,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose9,
            after_pose_func=self.after_pose9,
        )
        self.poses.append(self._pose9)

        # 10: drive north to raw x=880 (out of the NinjaDropZone area),
        # preserving the current y. End facing north (raw 0°). Target
        # computed at runtime from pose_current.
        self._pose10 = Pose(
            x=0,
            y=0,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose10,
            after_pose_func=self.after_pose10,
        )
        self.poses.append(self._pose10)

        if self.planner.shared_properties.table == TableEnum.Training:
            for pose in self.poses:
                pose.x -= 1000

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)
        # First deposit is done: drop the start-area DropZone so the
        # subsequent shake/recul poses can drive through it.
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDropZone].enabled = False
        self.logger.info(f"{self.name}: after_pose1 - NinjaDropZone disabled")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def before_pose2(self):
        self.logger.info(f"{self.name}: before_pose2 - deploying arms_side")

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2")
        # await actuators.ninja_arms_near_side(self.planner, speed=200)
        # await asyncio.sleep(5)
        await actuators.ninja_arms_side(self.planner, speed=1000)
        await asyncio.sleep(1)

    async def before_pose2b(self):
        self.logger.info(f"{self.name}: before_pose2")

    async def after_pose2b(self):
        self.logger.info(f"{self.name}: after_pose2")

    async def after_pose3(self):
        self.logger.info(f"{self.name}: after_pose3")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    # async def after_pose4(self):
    #    self.logger.info(f"{self.name}: after_pose4")

    # async def after_pose5(self):
    #    self.logger.info(f"{self.name}: after_pose5")
    #    await actuators.ninja_arms_open(self.planner, speed=0)
    #    await asyncio.sleep(0.5)

    async def before_pose6(self):
        self.logger.info(f"{self.name}: before_pose6 - closing arms")

    async def after_pose6(self):
        self.logger.info(f"{self.name}: after_pose6")
        await actuators.ninja_arms_close(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose6b(self):
        self.logger.info(f"{self.name}: after_pose6b")

    async def before_pose7(self):
        self.logger.info(f"{self.name}: before_pose7 - re-enabling NinjaDropZone")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDropZone].enabled = True
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def after_pose7(self):
        self.logger.info(f"{self.name}: after_pose7")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDropZone].enabled = False
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def before_pose8(self):
        cur = self.planner.pose_current
        # 120 mm east in display = raw y decrease (user-frame east = y-).
        # End facing west in display (raw +90°) so the BACKWARD motion
        # direction is east. AdaptedPose wraps the deltas so the sign is
        # camp-correct (y- east in blue stays y- east; in yellow it flips).
        delta = AdaptedPose(x=0, y=-self.DROP_FOUR_8_EAST_MM, O=90)
        self._pose8.x = cur.x + delta.x
        self._pose8.y = cur.y + delta.y
        self._pose8.O = delta.O
        self.logger.info(
            f"{self.name}: before_pose8 target ({self._pose8.x:.1f}, "
            f"{self._pose8.y:.1f}, {self._pose8.O:.1f}) from "
            f"current ({cur.x:.1f}, {cur.y:.1f}, {cur.O:.1f})"
        )

    async def after_pose8(self):
        self.logger.info(f"{self.name}: after_pose8")

    async def before_pose9(self):
        cur = self.planner.pose_current
        # 40 mm west in display (operating frame: west = raw +y). FORWARD
        # motion with end heading raw +90° (facing west) so forward direction
        # is west. AdaptedPose wraps the deltas to stay camp-correct.
        delta = AdaptedPose(x=0, y=self.DROP_FOUR_9_WEST_MM, O=90)
        self._pose9.x = cur.x + delta.x
        self._pose9.y = cur.y + delta.y
        self._pose9.O = delta.O
        self.logger.info(
            f"{self.name}: before_pose9 target ({self._pose9.x:.1f}, "
            f"{self._pose9.y:.1f}, {self._pose9.O:.1f}) from "
            f"current ({cur.x:.1f}, {cur.y:.1f}, {cur.O:.1f})"
        )

    async def after_pose9(self):
        self.logger.info(f"{self.name}: after_pose9")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDropZone].enabled = False
        self.logger.info(f"{self.name}: after_pose9 - NinjaDropZone disabled")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaCratesZone].enabled = True
        self.logger.info(f"{self.name}: after_pose9 - NinjaCratesZone enabled")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def before_pose10(self):
        cur = self.planner.pose_current
        # Drive north to raw x=DROP_FOUR_10_X_TARGET while preserving y.
        # End facing north (raw 0°).
        self._pose10.x = self.DROP_FOUR_10_X_TARGET
        self._pose10.y = cur.y
        self._pose10.O = 0
        self.logger.info(
            f"{self.name}: before_pose10 target ({self._pose10.x:.1f}, "
            f"{self._pose10.y:.1f}, {self._pose10.O:.1f}) from "
            f"current ({cur.x:.1f}, {cur.y:.1f}, {cur.O:.1f})"
        )

    async def after_pose10(self):
        self.logger.info(f"{self.name}: after_pose10")

    def weight(self) -> float:
        # Highest weight: runs first in the standalone strategy.
        return 11_000_000.0


class NinjaBuildGroupAction(Action):
    """
    Build the Ninja group of 4: pickup sequence collecting the four items
    (left side and top side of the start area) and stacking them into a
    holdable group, ready to be carried to the pantry.
    """

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = False):
        super().__init__("Ninja build group", planner, strategy, interruptable=True)
        self.before_action_func = self.before_action
        self.wait = wait

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def before_action(self):
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

        # Disable NinjaArea1 immediately: poses 1 to 5b operate inside the
        # inflated obstacle (the avoidance inflates by robot_width=160 mm, so
        # Area1 effective x range becomes 570..880 and y range -530..-270,
        # which already swallows pose 2 at (840, -400)).
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaArea1].enabled = False
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

        # Anchors at the centers of the two nut crate zones (raw blue coords).
        # Wrapping each relative-pose result in AdaptedPose camp-adapts y and O.
        area1_anchor = Pose(x=725, y=-400, O=0)
        area2_anchor = Pose(x=775, y=-150, O=0)

        # === Area 1 (poses 1..5b) ===

        pose1 = AdaptedPose(
            **get_relative_pose(area1_anchor, front_offset=165, side_offset=0, angular_offset=180).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        pose2 = AdaptedPose(
            **get_relative_pose(area1_anchor, front_offset=115, side_offset=0, angular_offset=0).model_dump(),
            max_speed_linear=10,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose2)

        pose3 = AdaptedPose(
            **get_relative_pose(area1_anchor, front_offset=165, side_offset=0, angular_offset=0).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose3)

        pose4 = AdaptedPose(
            **get_relative_pose(area1_anchor, front_offset=25, side_offset=0, angular_offset=180).model_dump(),
            max_speed_linear=10,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose4,
        )
        self.poses.append(pose4)

        pose5b = AdaptedPose(
            **get_relative_pose(area1_anchor, front_offset=75, side_offset=0, angular_offset=-90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose5b,
        )
        self.poses.append(pose5b)

        # === Transition + Area 2 (poses 6..16) ===

        pose6 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=0, side_offset=-125, angular_offset=-90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose6,
            after_pose_func=self.after_pose6,
        )
        self.poses.append(pose6)

        pose7 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=0, side_offset=-50, angular_offset=0).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose7,
        )
        self.poses.append(pose7)

        pose8 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=0, side_offset=-75, angular_offset=-90).model_dump(),
            max_speed_linear=20,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose8,
        )
        self.poses.append(pose8)

        pose9 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=-125, side_offset=0, angular_offset=90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose9,
        )
        self.poses.append(pose9)

        pose10 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=-125, side_offset=-50, angular_offset=90).model_dump(),
            max_speed_linear=33,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose10,
        )
        self.poses.append(pose10)

        pose11 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=-125, side_offset=0, angular_offset=90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose11,
        )
        self.poses.append(pose11)

        pose12 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=0, side_offset=-50, angular_offset=-90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose12,
        )
        self.poses.append(pose12)

        pose13 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=0, side_offset=50, angular_offset=-90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose13,
        )
        self.poses.append(pose13)

        pose14 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=-125, side_offset=50, angular_offset=90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose14,
        )
        self.poses.append(pose14)

        pose15 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=-125, side_offset=-10, angular_offset=90).model_dump(),
            max_speed_linear=20,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose15,
        )
        self.poses.append(pose15)

        pose16 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=-125, side_offset=90, angular_offset=90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose16,
        )
        self.poses.append(pose16)

        if self.planner.shared_properties.table == TableEnum.Training:
            for pose in self.poses:
                pose.x -= 1000

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2")

    async def after_pose3(self):
        self.logger.info(f"{self.name}: after_pose3")

    async def after_pose4(self):
        self.logger.info(f"{self.name}: after_pose4")

    async def after_pose5b(self):
        self.logger.info(f"{self.name}: after_pose5b")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def before_pose6(self):
        self.logger.info(f"{self.name}: before_pose6 - disabling NinjaArea2")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaArea2].enabled = False
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def after_pose6(self):
        self.logger.info(f"{self.name}: after_pose6")
        await actuators.ninja_arms_hold_one_long(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose7(self):
        self.logger.info(f"{self.name}: after_pose7")

    async def after_pose8(self):
        self.logger.info(f"{self.name}: after_pose8")

    async def after_pose9(self):
        self.logger.info(f"{self.name}: after_pose9")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose10(self):
        self.logger.info(f"{self.name}: after_pose10")

    async def after_pose11(self):
        self.logger.info(f"{self.name}: after_pose11")
        await actuators.ninja_arms_close(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose12(self):
        self.logger.info(f"{self.name}: after_pose12")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose13(self):
        self.logger.info(f"{self.name}: after_pose13")
        await actuators.ninja_arms_hold_one_long(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose14(self):
        self.logger.info(f"{self.name}: after_pose14")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose15(self):
        self.logger.info(f"{self.name}: after_pose15")

    async def after_pose16(self):
        self.logger.info(f"{self.name}: after_pose16")
        await actuators.ninja_arms_close(self.planner, speed=0)
        await asyncio.sleep(0.5)

    def weight(self) -> float:
        # Higher weight than NinjaPantryDepositAction so the strategy picks
        # the build group first (Strategy.get_next_action sorts by weight
        # ascending and takes the last entry).
        return 10_000_000.0


class NinjaPantryDepositAction(Action):
    """
    Deposit the assembled group at the pantry: travel from the build area
    to the pantry, drop the items in two passes, and clear out.
    """

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = False):
        super().__init__("Ninja pantry deposit", planner, strategy, interruptable=True)
        self.before_action_func = self.before_action
        self.wait = wait

    async def before_action(self):
        # NinjaArea1 and NinjaArea2 are expected to be already disabled by
        # NinjaBuildGroupAction which always runs before us (higher weight).
        # Enable NinjaDeposit so the released crates show on the monitor
        # and the avoidance routes around them for the rest of the action.
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDeposit].enabled = True
        self.logger.info(f"{self.name}: NinjaDeposit enabled")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

        area1_anchor = Pose(x=725, y=-400, O=0)
        deposit_obstacle = self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDeposit]
        deposit_anchor = Pose(x=deposit_obstacle.x, y=deposit_obstacle.y, O=0)

        # 17: drive 205 mm north of the deposit zone center, aligned on its
        # Y axis. Raw (880, -250, 0°) → display (880, +250, 0°). Facing
        # north. front_offset capped at 205 mm so the robot front edge
        # stays inside the table (raw x_max = 1000, robot half-length 77).
        pose17 = AdaptedPose(
            **get_relative_pose(deposit_anchor, front_offset=205, side_offset=0, angular_offset=0).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose17,
        )
        self.poses.append(pose17)

        # 18: descend to x=750 along the same heading (0°), driving backward
        # since the robot is facing north. Part of the N-S corridor poses
        # 17→18→19. Target inside NinjaDeposit inflated bbox, so disable in
        # before_pose18 and re-enable in before_pose20.
        pose18 = AdaptedPose(
            **get_relative_pose(area1_anchor, front_offset=25, side_offset=150, angular_offset=0).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose18,
            after_pose_func=self.after_pose18,
        )
        self.poses.append(pose18)

        # 19: climb back north to x=880, still facing north (forward).
        pose19 = AdaptedPose(
            **get_relative_pose(area1_anchor, front_offset=155, side_offset=150, angular_offset=0).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose19,
        )
        self.poses.append(pose19)

        # 20: park east of the NinjaDeposit zone facing west, reached
        # forward. Re-enable NinjaDeposit (disabled by pose 18) so the
        # avoidance plans the detour around the released crates.
        pose20 = AdaptedPose(
            **get_relative_pose(deposit_anchor, front_offset=-40, side_offset=-350, angular_offset=90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose20,
            after_pose_func=self.after_pose20,
        )
        self.poses.append(pose20)

        # 21: drive west backward to 10 mm east of the zone's east edge.
        pose21 = AdaptedPose(
            **get_relative_pose(deposit_anchor, front_offset=-40, side_offset=-180, angular_offset=-90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose21,
        )
        self.poses.append(pose21)

        # 22: back up 50 mm east of pose 21.
        pose22 = AdaptedPose(
            **get_relative_pose(deposit_anchor, front_offset=-40, side_offset=-230, angular_offset=90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose22,
        )
        self.poses.append(pose22)

        # 23/24/25: replay the N-S-N corridor of poses 17→18→19 with a
        # deeper south dip (x=625) for the second pass.
        pose23 = AdaptedPose(
            **get_relative_pose(deposit_anchor, front_offset=205, side_offset=0, angular_offset=0).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose23,
        )
        self.poses.append(pose23)

        pose24 = AdaptedPose(
            **get_relative_pose(deposit_anchor, front_offset=-60, side_offset=0, angular_offset=0).model_dump(),
            max_speed_linear=20,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose24,
            after_pose_func=self.after_pose24,
        )
        self.poses.append(pose24)

        pose25 = AdaptedPose(
            **get_relative_pose(deposit_anchor, front_offset=205, side_offset=0, angular_offset=0).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose25,
        )
        self.poses.append(pose25)

        if self.planner.shared_properties.table == TableEnum.Training:
            for pose in self.poses:
                pose.x -= 1000

    async def after_pose17(self):
        self.logger.info(f"{self.name}: after_pose17")

    async def before_pose18(self):
        self.logger.info(f"{self.name}: before_pose18 - disabling NinjaDeposit")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDeposit].enabled = False
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def after_pose18(self):
        self.logger.info(f"{self.name}: after_pose18")

    async def after_pose19(self):
        self.logger.info(f"{self.name}: after_pose19")

    async def before_pose20(self):
        self.logger.info(f"{self.name}: before_pose20 - enabling NinjaDeposit")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDeposit].enabled = True
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def after_pose20(self):
        self.logger.info(f"{self.name}: after_pose20")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDeposit].enabled = False
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def after_pose21(self):
        self.logger.info(f"{self.name}: after_pose21")

    async def after_pose22(self):
        self.logger.info(f"{self.name}: after_pose22")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDeposit].enabled = True
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def after_pose23(self):
        self.logger.info(f"{self.name}: after_pose23")

    async def before_pose24(self):
        self.logger.info(f"{self.name}: before_pose24 - disabling NinjaDeposit")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDeposit].enabled = False
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def after_pose24(self):
        self.logger.info(f"{self.name}: after_pose24")

    async def after_pose25(self):
        self.logger.info(f"{self.name}: after_pose25")
        # PantryDeposit done: drop the NinjaDeposit obstacle so the next
        # actions can move freely through the deposit area.
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDeposit].enabled = False
        self.logger.info(f"{self.name}: after_pose25 - NinjaDeposit disabled")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    def weight(self) -> float:
        # Dependency guard: do not run until NinjaBuildGroupAction has been
        # completed (it is removed from the strategy when picked).
        if any(isinstance(a, NinjaBuildGroupAction) for a in self.strategy):
            return 0
        return 9_999_999.0


class NinjaRottenDepositAction(Action):
    """
    Pick up two crates from NinjaCratesZone one at a time and deposit them
    at the rotten zone (reuse the existing arms_open coords from the
    original action). Each pickup uses `arms_hold_one_long`.
    """

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = False):
        super().__init__("Ninja rotten deposit", planner, strategy, interruptable=True)
        self.before_action_func = self.before_action
        self.wait = wait

    async def before_action(self):
        # Disable NinjaCratesZone so the pickup poses (inside the inflated
        # bbox) are accepted by the avoidance. The crates' physical presence
        # is handled by the pose offsets below.
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaCratesZone].enabled = False
        self.logger.info(f"{self.name}: NinjaCratesZone disabled")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

        # Approach: 40 mm west of pickup 1 (raw y +40 in operating frame).
        # Robot stops here and opens its arms before moving to the first
        # crate, so the arms are already open at pickup time.
        pose_approach = AdaptedPose(
            x=675,
            y=-550,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose_approach,
        )
        self.poses.append(pose_approach)

        # 1: pickup 1 at the DropFour pose 8 position (675, -635, +90°),
        # facing west toward the crate. Reached BACKWARD from pose_approach
        # so the rear of the robot leads into the crate. arms_hold_one_long
        # grabs the first crate after arrival.
        pose1 = AdaptedPose(
            x=675,
            y=-635,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        # Clearance after pickup 1: 100 mm full west of pickup 1 so the
        # robot exits the crates zone in a straight line before turning
        # toward the deposit. FORWARD since the robot is already facing
        # west after pose 1.
        pose1_clear = AdaptedPose(
            x=675,
            y=-535,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose1_clear,
        )
        self.poses.append(pose1_clear)

        # 2: deposit 1 at (775, -280, -90°). arms_open at arrival.
        pose2 = AdaptedPose(
            x=775,
            y=-200,
            O=-90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose2)

        # Approach 2: 85 mm west of pickup 2, mirroring the first approach.
        # Robot stops here and re-opens its arms before the BACKWARD pickup.
        pose_approach2 = AdaptedPose(
            x=675,
            y=-600,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose_approach2,
        )
        self.poses.append(pose_approach2)

        # 3: pickup 2 at (675, -685, +90°) — 50 mm east of pickup 1 in the
        # operating frame. Reached BACKWARD from pose_approach2.
        # before_pose3 shrinks the crates zone by 50 mm (one crate already
        # removed) and shifts its center 25 mm east.
        pose3 = AdaptedPose(
            x=675,
            y=-685,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose3,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose3)

        # 4: deposit 2 at (725, -250, 90°). arms_open at arrival.
        pose4 = AdaptedPose(
            x=725,
            y=-250,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose4,
        )
        self.poses.append(pose4)

        # 5: deposit 2 at (725, -200, 90°). arms_close at arrival.
        pose5 = AdaptedPose(
            x=725,
            y=-200,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose5,
        )
        self.poses.append(pose5)

        if self.planner.shared_properties.table == TableEnum.Training:
            for pose in self.poses:
                pose.x -= 1000

    async def after_pose_approach(self):
        self.logger.info(f"{self.name}: after_pose_approach - opening arms")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaCratesZone].enabled = False
        self.logger.info(f"{self.name}: after_pose9 - NinjaCratesZone disabled")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1 - pickup 1")
        await actuators.ninja_arms_hold_one_long(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose1_clear(self):
        self.logger.info(f"{self.name}: after_pose1_clear")

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2 - deposit 1")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose_approach2(self):
        self.logger.info(f"{self.name}: after_pose_approach2 - opening arms")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def before_pose3(self):
        # First crate removed: shrink the crates zone by 50 mm along y and
        # shift its center 25 mm east so the remaining 2 crates are still
        # represented accurately. The avoidance picks up the new shape via
        # the next update_obstacles cycle.
        zone = self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaCratesZone]
        zone.length -= 50
        zone.y -= 25
        self.logger.info(f"{self.name}: before_pose3 - NinjaCratesZone shrunk (length={zone.length}, y={zone.y})")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def after_pose3(self):
        self.logger.info(f"{self.name}: after_pose3 - pickup 2")
        await actuators.ninja_arms_hold_one_long(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose4(self):
        self.logger.info(f"{self.name}: after_pose4 - deposit 2")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose5(self):
        self.logger.info(f"{self.name}: after_pose5 - close")
        await actuators.ninja_arms_close(self.planner, speed=0)
        await asyncio.sleep(0.5)

    def weight(self) -> float:
        return 9_500_000.0


class NinjaAtTableAction(Action):
    """
    Final celebration: drive to the dinner spot and oscillate the arms forever.
    """

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = False):
        super().__init__("Ninja a table", planner, strategy, interruptable=True)
        self.before_action_func = self.before_action
        self.wait = wait

    async def before_action(self):
        pose3 = AdaptedPose(
            x=620,
            y=-200,
            O=45,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose3,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose3)

        if self.planner.shared_properties.table == TableEnum.Training:
            for pose in self.poses:
                pose.x -= 1000

    async def before_pose3(self):
        self.logger.info(f"{self.name}: before_pose3 - disabling all fixed obstacles")
        for obstacle in self.planner.game_context.fixed_obstacles.values():
            obstacle.enabled = False
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def after_pose3(self):
        self.logger.info(f"{self.name}: after_pose3 - oscillating arms until reset")
        try:
            while self.planner.playing:
                await actuators.ninja_arms_open(self.planner, speed=0)
                await asyncio.sleep(0.5)
                if not self.planner.playing:
                    break
                await actuators.ninja_arms_close(self.planner, speed=0)
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            self.logger.info(f"{self.name}: arm oscillation cancelled")
            raise
        self.logger.info(f"{self.name}: arm oscillation stopped (playing=False)")

    def weight(self) -> float:
        if self.planner.game_context.countdown > 5:
            return 0
        return 99_999_999.0


class NinjaHomologationAction(Action):
    """
    Homologation run: disables every Ninja fixed obstacle and traces a
    fixed 4-pose path at full speed in FORWARD with bypass_final_orientation
    so the robot keeps moving without rotating to the target heading at
    each waypoint.
    """

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = False):
        super().__init__("Ninja homologation", planner, strategy, interruptable=True)
        self.before_action_func = self.before_action
        self.wait = wait

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def before_action(self):
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

        # Disable every Ninja-specific fixed obstacle so the avoidance has
        # a clean path for the homologation course.
        for obstacle_id in (
            FixedObstacleID.NinjaArea1,
            FixedObstacleID.NinjaArea2,
            FixedObstacleID.NinjaDeposit,
            FixedObstacleID.NinjaDropZone,
            FixedObstacleID.NinjaCratesZone,
        ):
            self.planner.game_context.fixed_obstacles[obstacle_id].enabled = False
        self.logger.info(f"{self.name}: all Ninja obstacles disabled")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

        waypoints = [
            (880, -600, 0),
            (750, -600, 0),
            (750, -100, 0),
            (880, -750, 90),
        ]
        for x, y, o in waypoints:
            self.poses.append(
                AdaptedPose(
                    x=x,
                    y=y,
                    O=o,
                    max_speed_linear=20,
                    max_speed_angular=100,
                    motion_direction=MotionDirection.FORWARD_ONLY,
                    bypass_final_orientation=True,
                )
            )

        if self.planner.shared_properties.table == TableEnum.Training:
            for pose in self.poses:
                pose.x -= 1000

    def weight(self) -> float:
        return 9_999_999.0


class NinjaStandaloneStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        # can_wait keeps a WaitAction running between regular actions so the
        # blocked() preemption at T-5s has something to interrupt, instead of
        # an idle planner (self.action == None silently skipped in blocked()).
        self.can_wait = True
        # self.append(NinjaExposeFourAction(planner, self))
        self.append(NinjaDropFourAction(planner, self))
        self.append(NinjaBuildGroupAction(planner, self))
        self.append(NinjaPantryDepositAction(planner, self))
        self.append(NinjaRottenDepositAction(planner, self))
        self.append(NinjaAtTableAction(planner, self))
        # self.append(NinjaHomologationAction(planner, self))
