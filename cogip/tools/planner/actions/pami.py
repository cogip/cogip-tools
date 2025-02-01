import asyncio
import math
from typing import TYPE_CHECKING

from colorzero import Color

from cogip.models import models
from cogip.tools.planner import logger
from cogip.tools.planner.actions.actions import Action, Actions, get_relative_pose
from cogip.tools.planner.avoidance.avoidance import AvoidanceStrategy
from cogip.tools.planner.camp import Camp
from cogip.tools.planner.pose import AdaptedPose, Pose

if TYPE_CHECKING:
    from ..planner import Planner


class PamiAction(Action):
    """
    PAMI action.
    """

    def __init__(self, planner: "Planner", actions: Actions, *, x: int, y: int, margin: int, start_delay: int):
        super().__init__("PAMI action", planner, actions, interruptable=False)
        self.before_action_func = self.before_action
        self.destination = models.Pose(x=x, y=y)
        self.margin = margin
        self.start_delay = start_delay

    async def before_action(self):
        await self.planner.pami_event.wait()

        self.start_pose = self.pose_current.model_copy()

        forward_pose = Pose(
            **get_relative_pose(
                self.start_pose,
                front_offset=self.game_context.properties.robot_length,
            ).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            allow_reverse=False,
            before_pose_func=self.before_forward,
            after_pose_func=self.after_forward,
        )
        self.poses.append(forward_pose)

        dist_x = self.destination.x - self.start_pose.x
        dist_y = self.destination.y - self.start_pose.y
        dist = math.hypot(dist_x, dist_y)

        self.pose = AdaptedPose(
            x=self.destination.x - dist_x / dist * self.margin,
            y=self.destination.y - dist_y / dist * self.margin,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            allow_reverse=False,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose,
            intermediate_pose_func=self.intermediate_pose,
            after_pose_func=self.after_pose,
        )
        self.poses.append(self.pose)

    async def before_forward(self):
        logger.info(f"{self.name}: before_forward")
        self.planner.led.color = Color("lightblue")
        await asyncio.sleep(self.start_delay)
        self.planner.led.color = Color("green")

    async def after_forward(self):
        logger.info(f"{self.name}: after_forward")

    async def before_pose(self):
        logger.info(f"{self.name}: before_pose - pose={self.pose.model_dump(include=["x", "y"])}")

    async def intermediate_pose(self):
        # Update pose to take avoidance into account
        pose_current = self.pose_current.model_copy()
        dist_x = self.destination.x - pose_current.x
        dist_y = Camp().adapt_y(self.destination.y - pose_current.y)
        dist = math.hypot(dist_x, dist_y)
        self.planner.pose_order.x = self.destination.x - dist_x / dist * self.margin
        self.planner.pose_order.y = Camp().adapt_y(self.destination.y - dist_y / dist * self.margin)
        self.planner.shared_properties["pose_order"] = self.planner.pose_order.path_pose.model_dump(exclude_unset=True)
        logger.info(f"{self.name}: intermediate_pose - pose={self.planner.pose_order.model_dump(include=['x', 'y'])}")

    async def after_pose(self):
        logger.info(f"{self.name}: after_pose")
        self.planner.led.color = Color("red")
        self.actions.clear()

    def weight(self) -> float:
        return 9_999_999.0


class Pami5Action(Action):
    """
    PAMI 5 action.
    """

    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__("PAMI 5 action", planner, actions, interruptable=False)
        self.before_action_func = self.before_action

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.game_context.avoidance_strategy = new_strategy
        self.planner.shared_properties["avoidance_strategy"] = new_strategy

    async def before_action(self):
        self.planner.properties.disable_fixed_obstacles = True

        await self.planner.pami_event.wait()

        self.start_pose = self.pose_current.model_copy()
        self.avoidance_backup = self.game_context.avoidance_strategy

        pose1 = AdaptedPose(
            x=self.start_pose.x,
            y=-300,
            max_speed_linear=100,
            max_speed_angular=100,
            allow_reverse=False,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose1,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        pose2 = AdaptedPose(
            x=610,
            y=-300,
            O=180,
            max_speed_linear=20,
            max_speed_angular=50,
            allow_reverse=False,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose2,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose2)

    async def before_pose1(self):
        logger.info(f"{self.name}: before_pose1")
        self.set_avoidance(AvoidanceStrategy.Disabled)
        self.planner.led.color = Color("green")

    async def after_pose1(self):
        logger.info(f"{self.name}: after_pose1")
        self.set_avoidance(self.avoidance_backup)

    async def before_pose2(self):
        logger.info(f"{self.name}: before_pose2")

    async def after_pose2(self):
        logger.info(f"{self.name}: after_pose2")
        self.planner.led.color = Color("red")
        self.actions.clear()
        self.planner.properties.disable_fixed_obstacles = False

    def weight(self) -> float:
        return 9_999_999.0


class Pami2Actions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(PamiAction(planner, self, x=430, y=340, margin=100, start_delay=0))


class Pami3Actions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(PamiAction(planner, self, x=390, y=-120, margin=100, start_delay=3))


class Pami4Actions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(PamiAction(planner, self, x=410, y=-390, margin=50, start_delay=6))


class Pami5Actions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(Pami5Action(planner, self))
