import asyncio
import math
from typing import TYPE_CHECKING

from colorzero import Color

from cogip.cpp.libraries.models import MotionDirection
from cogip.tools.planner import actuators
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.actions.utils import get_relative_pose, set_countdown_color
from cogip.tools.planner.avoidance.avoidance import AvoidanceStrategy
from cogip.tools.planner.pose import AdaptedPose, Pose
from cogip.tools.planner.table import TableEnum

if TYPE_CHECKING:
    from ..planner import Planner


class NinjaAction(Action):
    """
    Ninja action.
    """

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = True):
        super().__init__("Ninja action", planner, strategy, interruptable=False)
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
        super().__init__("Ninja expose four", planner, strategy, interruptable=False)
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

    DROP_FOUR_RECUL_MM = 210  # pose 2: back 220 mm from pose 1
    # DROP_FOUR_2A_BACKWARD_MM = 110  # pose 2a: back 110 mm from pose 2
    DROP_FOUR_2C_FORWARD_MM = 180  # pose 2c: forward 190 mm from pose 2
    DROP_FOUR_2D_BACKWARD_MM = 100  # pose 2d: back 100 mm from pose 2c
    DROP_FOUR_2E_FORWARD_MM = 100  # pose 2e: forward 100 mm from pose 2d
    DROP_FOUR_ADVANCE_MM = 175  # pose 2b: forward 175 mm from pose 2
    DROP_FOUR_PARK_FORWARD_MM = 40  # pose 5: 40 mm forward from pose 2e
    DROP_FOUR_PARK_ANGULAR_DEG = 90  # pose 5: +90 deg heading vs pose 2e

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = False):
        super().__init__("Ninja drop four", planner, strategy, interruptable=False)
        self.before_action_func = self.before_action
        self.wait = wait

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def before_action(self):
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

        pose_approach = AdaptedPose(
            x=880,
            y=-500,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose_approach,
        )
        self.poses.append(pose_approach)

        pose1 = AdaptedPose(
            x=880,
            y=-690,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BIDIRECTIONAL,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        # 2: recul 150 mm relative to pose 1 (along pose 1's heading axis).
        # arms_side fires at the start (before_pose_func) so the deployment
        # runs in parallel with the BWD drive rather than waiting at the end.
        pose2 = Pose(
            **get_relative_pose(pose1, front_offset=-self.DROP_FOUR_RECUL_MM).model_dump(),
            max_speed_linear=10,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose2,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose2)

        # 2b: advance 175 mm relative to pose 2 (commented out for now).
        # pose2b = Pose(
        #     **get_relative_pose(pose2, front_offset=self.DROP_FOUR_ADVANCE_MM).model_dump(),
        #     max_speed_linear=10,
        #     max_speed_angular=100,
        #     motion_direction=MotionDirection.FORWARD_ONLY,
        #     bypass_final_orientation=True,
        #     after_pose_func=self.after_pose2b,
        # )
        # self.poses.append(pose2b)

        # 2a: recul 110 mm relative to pose 2, no servo action.
        # pose2a = Pose(
        #    **get_relative_pose(pose2, front_offset=-self.DROP_FOUR_2A_BACKWARD_MM).model_dump(),
        #    max_speed_linear=10,
        #    max_speed_angular=100,
        #    motion_direction=MotionDirection.BACKWARD_ONLY,
        #    bypass_final_orientation=True,
        #    after_pose_func=self.after_pose2a,
        # )
        # self.poses.append(pose2a)

        # 2c: advance 190 mm relative to pose 2, no servo action.
        pose2c = Pose(
            **get_relative_pose(pose2, front_offset=self.DROP_FOUR_2C_FORWARD_MM).model_dump(),
            max_speed_linear=10,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose2c,
        )
        self.poses.append(pose2c)

        # 2d: recul 100 mm relative to pose 2c, no servo action.
        pose2d = Pose(
            **get_relative_pose(pose2c, front_offset=-self.DROP_FOUR_2D_BACKWARD_MM).model_dump(),
            max_speed_linear=10,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose2d,
        )
        self.poses.append(pose2d)

        # 2e: advance 100 mm relative to pose 2d, opens arms at the end.
        pose2e = Pose(
            **get_relative_pose(pose2d, front_offset=self.DROP_FOUR_2E_FORWARD_MM).model_dump(),
            max_speed_linear=10,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose2e,
        )
        self.poses.append(pose2e)

        # 5: park 40 mm further forward with +90 deg heading relative to pose 2e.
        pose5 = Pose(
            **get_relative_pose(
                pose2e,
                front_offset=self.DROP_FOUR_PARK_FORWARD_MM,
                angular_offset=self.DROP_FOUR_PARK_ANGULAR_DEG,
            ).model_dump(),
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
        self.logger.info(f"{self.name}: after_pose_approach")

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(2)

    async def before_pose2(self):
        self.logger.info(f"{self.name}: before_pose2 - deploying arms_side")
        await actuators.ninja_arms_side(self.planner, speed=150)

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2")
        await asyncio.sleep(3)

    async def after_pose2a(self):
        self.logger.info(f"{self.name}: after_pose2a")

    async def after_pose2b(self):
        self.logger.info(f"{self.name}: after_pose2b")

    async def after_pose2c(self):
        self.logger.info(f"{self.name}: after_pose2c")

    async def after_pose2d(self):
        self.logger.info(f"{self.name}: after_pose2d")

    async def after_pose2e(self):
        self.logger.info(f"{self.name}: after_pose2e")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose5(self):
        self.logger.info(f"{self.name}: after_pose5")
        await actuators.ninja_arms_close(self.planner, speed=0)
        await asyncio.sleep(0.5)

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
        super().__init__("Ninja build group", planner, strategy, interruptable=False)
        self.before_action_func = self.before_action
        self.wait = wait

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def before_action(self):
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

        pose1 = AdaptedPose(
            x=890,
            y=-400,
            O=180,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        pose2 = AdaptedPose(
            x=840,
            y=-400,
            O=0,
            max_speed_linear=10,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose2)

        pose3 = AdaptedPose(
            x=890,
            y=-400,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose3)

        pose4 = AdaptedPose(
            x=750,
            y=-400,
            O=180,
            max_speed_linear=10,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose4,
        )
        self.poses.append(pose4)

        pose5b = AdaptedPose(
            x=800,
            y=-400,
            O=-90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose5b,
        )
        self.poses.append(pose5b)

        pose6 = AdaptedPose(
            x=775,
            y=-275,
            O=-90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose6,
        )
        self.poses.append(pose6)

        pose7 = AdaptedPose(
            x=775,
            y=-200,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose7,
        )
        self.poses.append(pose7)

        pose8 = AdaptedPose(
            x=775,
            y=-225,
            O=-90,
            max_speed_linear=20,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose8,
        )
        self.poses.append(pose8)

        pose9 = AdaptedPose(
            x=650,
            y=-150,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose9,
        )
        self.poses.append(pose9)

        pose10 = AdaptedPose(
            x=650,
            y=-200,
            O=90,
            max_speed_linear=33,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose10,
        )
        self.poses.append(pose10)

        pose11 = AdaptedPose(
            x=650,
            y=-150,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose11,
        )
        self.poses.append(pose11)

        pose12 = AdaptedPose(
            x=775,
            y=-200,
            O=-90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose12,
        )
        self.poses.append(pose12)

        pose13 = AdaptedPose(
            x=775,
            y=-100,
            O=-90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose13,
        )
        self.poses.append(pose13)

        pose14 = AdaptedPose(
            x=650,
            y=-100,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose14,
        )
        self.poses.append(pose14)

        pose15 = AdaptedPose(
            x=650,
            y=-160,
            O=90,
            max_speed_linear=20,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose15,
        )
        self.poses.append(pose15)

        pose16 = AdaptedPose(
            x=650,
            y=-100,
            O=90,
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
        super().__init__("Ninja pantry deposit", planner, strategy, interruptable=False)
        self.before_action_func = self.before_action
        self.wait = wait

    async def before_action(self):
        pose1 = AdaptedPose(
            x=880,
            y=-100,
            O=90,
            max_speed_linear=66,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        pose2 = AdaptedPose(
            x=880,
            y=-350,
            O=0,
            max_speed_linear=66,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose2)

        pose3 = AdaptedPose(
            x=725,
            y=-350,
            O=0,
            max_speed_linear=20,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose3)

        pose4 = AdaptedPose(
            x=880,
            y=-250,
            O=0,
            max_speed_linear=20,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose4,
        )
        self.poses.append(pose4)

        pose5 = AdaptedPose(
            x=620,
            y=-250,
            O=0,
            max_speed_linear=20,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose5,
        )
        self.poses.append(pose5)

        pose6 = AdaptedPose(
            x=715,
            y=-250,
            O=0,
            max_speed_linear=66,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose6,
        )
        self.poses.append(pose6)

        if self.planner.shared_properties.table == TableEnum.Training:
            for pose in self.poses:
                pose.x -= 1000

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose3(self):
        self.logger.info(f"{self.name}: after_pose3")
        await actuators.ninja_arms_close(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose4(self):
        self.logger.info(f"{self.name}: after_pose4")

    async def after_pose5(self):
        self.logger.info(f"{self.name}: after_pose5")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose6(self):
        self.logger.info(f"{self.name}: after_pose6")
        await actuators.ninja_arms_close(self.planner, speed=0)
        await asyncio.sleep(0.5)

    def weight(self) -> float:
        return 9_999_999.0


class NinjaRottenDepositAction(Action):
    """
    Deposit rotten boxes in their dedicated zone.
    """

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = False):
        super().__init__("Ninja rotten deposit", planner, strategy, interruptable=False)
        self.before_action_func = self.before_action
        self.wait = wait

    async def before_action(self):
        pose_approach = AdaptedPose(
            x=880,
            y=-490,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose_approach,
        )
        self.poses.append(pose_approach)

        pose1 = AdaptedPose(
            x=715,
            y=-490,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        pose2 = AdaptedPose(
            x=715,
            y=-550,
            O=90,
            max_speed_linear=20,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose2)

        pose3 = AdaptedPose(
            x=715,
            y=-300,
            O=-90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose3)

        pose3b = AdaptedPose(
            x=715,
            y=-500,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose3b,
        )
        self.poses.append(pose3b)

        pose4 = AdaptedPose(
            x=715,
            y=-600,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose4,
        )
        self.poses.append(pose4)

        pose5 = AdaptedPose(
            x=715,
            y=-275,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose5,
        )
        self.poses.append(pose5)

        pose6 = AdaptedPose(
            x=715,
            y=-200,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose6,
        )
        self.poses.append(pose6)

        if self.planner.shared_properties.table == TableEnum.Training:
            for pose in self.poses:
                pose.x -= 1000

    async def after_pose_approach(self):
        self.logger.info(f"{self.name}: after_pose_approach")

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2")
        await actuators.ninja_arms_hold_one_long(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose3(self):
        self.logger.info(f"{self.name}: after_pose3")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose3b(self):
        self.logger.info(f"{self.name}: after_pose3b")

    async def after_pose4(self):
        self.logger.info(f"{self.name}: after_pose4")
        await actuators.ninja_arms_hold_one_long(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose5(self):
        self.logger.info(f"{self.name}: after_pose5")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose6(self):
        self.logger.info(f"{self.name}: after_pose6")
        await actuators.ninja_arms_close(self.planner, speed=0)
        await asyncio.sleep(0.5)

    def weight(self) -> float:
        return 9_500_000.0


class NinjaAtTableAction(Action):
    """
    Final celebration: drive to the dinner spot and oscillate the arms forever.
    """

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = False):
        super().__init__("Ninja a table", planner, strategy, interruptable=False)
        self.before_action_func = self.before_action
        self.wait = wait

    async def before_action(self):
        pose3 = AdaptedPose(
            x=600,
            y=-200,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose3)

        if self.planner.shared_properties.table == TableEnum.Training:
            for pose in self.poses:
                pose.x -= 1000

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
        return 9_000_000.0


class NinjaStandaloneStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        # NinjaExposeFourAction is the smooth-arc alternative to DropFour;
        # the two are concurrent so only one is active at a time.
        # self.append(NinjaExposeFourAction(planner, self))
        self.append(NinjaDropFourAction(planner, self))
        self.append(NinjaBuildGroupAction(planner, self))
        self.append(NinjaPantryDepositAction(planner, self))
        self.append(NinjaRottenDepositAction(planner, self))
        self.append(NinjaAtTableAction(planner, self))
