import asyncio
from typing import TYPE_CHECKING

from cogip import models
from cogip.cpp.libraries.models import MotionDirection
from cogip.tools.planner import actuators
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.pose import AdaptedPose, Pose

if TYPE_CHECKING:
    from ..planner import Planner


class RunAwayAction(Action):
    def __init__(self, planner: "Planner", strategy: Strategy):
        super().__init__("Run away action", planner, strategy, interruptable=True)
        self.before_action_func = self.before_action
        self.after_action_func = self.after_action

    def weight(self) -> float:
        if self.planner.game_context.countdown > 15:
            return 0
        if self.planner.game_context.countdown < 5:
            return 0

        return 9_999_000.0

    async def before_action(self):
        self.logger.info(f"{self.name}: before_action")
        self.planner.pose_order = None
        await self.planner.sio_ns.emit("brake")

        pose_bottom = AdaptedPose(x=-630, y=-1240, O=0)
        pose_top = AdaptedPose(x=130, y=-480, O=-90)
        pose_current = self.pose_current
        if pose_current.x > 200 or pose_current.y > -650:
            pose = pose_top
        else:
            pose = pose_bottom

        self.pose = Pose(
            x=pose.x,
            y=pose.y,
            O=pose.O,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BIDIRECTIONAL,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose,
            after_pose_func=self.after_pose,
        )
        self.poses.append(self.pose)

    async def after_action(self):
        # Keep only ParkingAction
        for action in self.strategy:
            if isinstance(action, ParkingAction):
                self.strategy.clear()
                self.strategy.append(action)
                break

    async def before_pose(self):
        self.logger.info(f"{self.name}: before_pose")

    async def after_pose(self):
        self.logger.info(f"{self.name}: after_pose")


class ParkingAction(Action):
    def __init__(self, planner: "Planner", strategy: Strategy, pose: models.Pose):
        super().__init__(f"Parking action at ({int(pose.x)}, {int(pose.y)})", planner, strategy, interruptable=False)
        self.parking_pose = pose
        self.before_action_func = self.before_action
        self.after_action_func = self.after_action

    def weight(self) -> float:
        if self.planner.game_context.countdown > 7:
            return 0

        return 9_999_000.0

    async def before_action(self):
        self.logger.info(f"{self.name}: before_action")
        self.strategy.can_wait = False
        self.planner.pose_order = None
        await self.planner.sio_ns.emit("brake")

        self.pose = Pose(
            x=self.parking_pose.x,
            y=self.parking_pose.y,
            O=self.parking_pose.O,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BIDIRECTIONAL,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose,
            after_pose_func=self.after_pose,
        )
        self.poses.append(self.pose)

    async def before_pose(self):
        self.logger.info(f"{self.name}: before_pose")

    async def after_pose(self):
        self.logger.info(f"{self.name}: after_pose")
        await actuators.front_arms_open(self.planner)
        duration = await actuators.back_arms_open(self.planner)
        await asyncio.sleep(duration)
        await actuators.front_grips_open(self.planner)
        await actuators.back_grips_open(self.planner)

    async def after_action(self):
        self.strategy.clear()
