import asyncio
from typing import TYPE_CHECKING

from colorzero import Color

from cogip.cpp.libraries.models import MotionDirection
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.actions.utils import get_relative_pose, set_countdown_color
from cogip.tools.planner.avoidance.avoidance import AvoidanceStrategy
from cogip.tools.planner.pose import AdaptedPose, Pose
from cogip.tools.planner.table import TableEnum

if TYPE_CHECKING:
    from ..planner import Planner


class Pami2Action(Action):
    """
    PAMI 2 action.
    """

    def __init__(self, planner: "Planner", strategy: Strategy, *, start_delay: int, wait: bool = True):
        super().__init__("PAMI 2 action", planner, strategy, interruptable=False)
        self.before_action_func = self.before_action
        self.start_delay = start_delay
        self.wait = wait

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def before_action(self):
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

        if self.wait:
            await self.planner.pami_event.wait()

        self.start_pose = self.pose_current.model_copy()

        pose0 = Pose(
            **get_relative_pose(
                self.start_pose,
                front_offset=self.planner.shared_properties.robot_length,
            ).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose0,
            after_pose_func=self.after_pose0,
        )
        self.poses.append(pose0)

        pose1 = AdaptedPose(
            x=150,
            y=-720,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose1,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        pose2 = AdaptedPose(
            x=150,
            y=0,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose2,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose2)

        final_pose = AdaptedPose(
            x=300,
            y=240,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_final,
            after_pose_func=self.after_final,
        )
        self.poses.append(final_pose)

        if self.planner.shared_properties.table == TableEnum.Training:
            pose0.x -= 1000
            pose1.x -= 1000
            pose2.x -= 1000
            pose2.y = -380
            final_pose.x = pose2.x
            final_pose.y = -180

    async def before_pose0(self):
        self.logger.info(f"{self.name}: before_pose0")
        self.set_avoidance(AvoidanceStrategy.Disabled)
        self.planner.led.color = Color("lightblue")
        await set_countdown_color(self.planner, "orange")
        await asyncio.sleep(self.start_delay)
        self.planner.led.color = Color("green")
        await set_countdown_color(self.planner, "green")

    async def after_pose0(self):
        self.logger.info(f"{self.name}: after_pose0")
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

    async def before_pose1(self):
        self.logger.info(f"{self.name}: before_pose1")

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")

    async def before_pose2(self):
        self.logger.info(f"{self.name}: before_pose2")

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2")

    async def before_final(self):
        self.logger.info(f"{self.name}: before_final")

    async def after_final(self):
        self.logger.info(f"{self.name}: after_final")
        self.planner.led.color = Color("red")
        await set_countdown_color(self.planner, "red")
        self.planner.flag_motor.on()
        self.strategy.clear()

    def weight(self) -> float:
        return 9_999_999.0


class Pami3Action(Action):
    """
    PAMI 3 action.
    """

    def __init__(self, planner: "Planner", strategy: Strategy, *, start_delay: int, wait: bool = True):
        super().__init__("PAMI 3 action", planner, strategy, interruptable=False)
        self.before_action_func = self.before_action
        self.start_delay = start_delay
        self.wait = wait

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def before_action(self):
        self.set_avoidance(AvoidanceStrategy.Disabled)

        if self.wait:
            await self.planner.pami_event.wait()

        self.start_pose = self.pose_current.model_copy()

        pose1 = Pose(
            **get_relative_pose(
                self.start_pose,
                front_offset=self.planner.shared_properties.robot_length,
            ).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose1,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        pose2 = AdaptedPose(
            x=340,
            y=-850,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose2,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose2)

        final_pose = AdaptedPose(
            x=340,
            y=-320,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_final,
            after_pose_func=self.after_final,
        )
        self.poses.append(final_pose)

        if self.planner.shared_properties.table == TableEnum.Training:
            pose1.x -= 1000
            pose2.x -= 1000
            final_pose.x -= 1000

    async def before_pose1(self):
        self.logger.info(f"{self.name}: before_pose1")
        self.set_avoidance(AvoidanceStrategy.Disabled)
        self.planner.led.color = Color("lightblue")
        await set_countdown_color(self.planner, "orange")
        await asyncio.sleep(self.start_delay)
        self.planner.led.color = Color("green")
        await set_countdown_color(self.planner, "green")

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

    async def before_pose2(self):
        self.logger.info(f"{self.name}: before_pose2")

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2")

    async def before_final(self):
        self.logger.info(f"{self.name}: before_final")

    async def after_final(self):
        self.logger.info(f"{self.name}: after_final")
        self.planner.led.color = Color("red")
        await set_countdown_color(self.planner, "red")
        self.planner.flag_motor.on()
        self.strategy.clear()

    def weight(self) -> float:
        return 9_999_999.0


class Pami4Action(Action):
    """
    PAMI 4 action.
    """

    def __init__(self, planner: "Planner", strategy: Strategy, *, start_delay: int, wait: bool = True):
        super().__init__("PAMI 4 action", planner, strategy, interruptable=False)
        self.before_action_func = self.before_action
        self.start_delay = start_delay
        self.wait = wait

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def before_action(self):
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

        if self.wait:
            await self.planner.pami_event.wait()

        self.start_pose = self.pose_current.model_copy()

        pose1 = Pose(
            **get_relative_pose(
                self.start_pose,
                front_offset=self.planner.shared_properties.robot_length,
            ).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose1,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        final_pose = AdaptedPose(
            x=530,
            y=-730,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_final,
            after_pose_func=self.after_final,
        )
        self.poses.append(final_pose)

        if self.planner.shared_properties.table == TableEnum.Training:
            pose1.x -= 1000
            final_pose.x -= 1000

    async def before_pose1(self):
        self.logger.info(f"{self.name}: before_pose1")
        self.set_avoidance(AvoidanceStrategy.Disabled)
        self.planner.led.color = Color("lightblue")
        await set_countdown_color(self.planner, "orange")
        await asyncio.sleep(self.start_delay)
        self.planner.led.color = Color("green")
        await set_countdown_color(self.planner, "green")

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

    async def before_final(self):
        self.logger.info(f"{self.name}: before_final")

    async def after_final(self):
        self.logger.info(f"{self.name}: after_final")
        self.planner.led.color = Color("red")
        await set_countdown_color(self.planner, "red")
        self.planner.flag_motor.on()
        self.strategy.clear()

    def weight(self) -> float:
        return 9_999_999.0


class Pami5Action(Action):
    """
    PAMI 5 action.
    """

    def __init__(self, planner: "Planner", strategy: Strategy, start_delay: int, wait: bool = True):
        super().__init__("PAMI 5 action", planner, strategy, interruptable=False)
        self.wait = wait
        self.before_action_func = self.before_action
        self.start_delay = start_delay

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def before_action(self):
        self.planner.shared_properties.disable_fixed_obstacles = True

        if self.wait:
            await self.planner.pami_event.wait()

        self.start_pose = self.pose_current.model_copy()

        pose1 = AdaptedPose(
            x=self.start_pose.x,
            y=-300,
            max_speed_linear=70,
            max_speed_angular=70,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose1,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        pose2 = AdaptedPose(
            x=610,
            y=-300,
            O=180,
            max_speed_linear=50,
            max_speed_angular=50,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose2,
            after_pose_func=self.after_pose2,
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            pose2.x -= 1000
        self.poses.append(pose2)

    async def before_pose1(self):
        self.logger.info(f"{self.name}: before_pose1")
        self.set_avoidance(AvoidanceStrategy.Disabled)
        self.planner.led.color = Color("lightblue")
        await set_countdown_color(self.planner, "orange")
        await asyncio.sleep(self.start_delay)
        self.planner.led.color = Color("green")
        await set_countdown_color(self.planner, "green")

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")

    async def before_pose2(self):
        self.logger.info(f"{self.name}: before_pose2")

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2")
        self.planner.led.color = Color("red")
        await set_countdown_color(self.planner, "red")
        self.strategy.clear()
        self.planner.shared_properties.disable_fixed_obstacles = False
        self.planner.flag_motor.on()

    def weight(self) -> float:
        return 9_999_999.0


class Pami2Strategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(Pami2Action(planner, self, start_delay=0))


class Pami3Strategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(Pami3Action(planner, self, start_delay=3))


class Pami4Strategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(Pami4Action(planner, self, start_delay=6))


class Pami5Strategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(Pami5Action(planner, self, start_delay=9))


# Standalone strategies


class Pami2StandaloneStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(Pami2Action(planner, self, start_delay=0, wait=False))


class Pami3StandaloneStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(Pami3Action(planner, self, start_delay=0, wait=False))


class Pami4StandaloneStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(Pami4Action(planner, self, start_delay=0, wait=False))


class Pami5StandaloneStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(Pami5Action(planner, self, start_delay=7, wait=False))
