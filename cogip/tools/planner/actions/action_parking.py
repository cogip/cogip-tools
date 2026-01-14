import asyncio
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from cogip import models
from cogip.cpp.libraries.models import MotionDirection
from cogip.tools.planner import actuators
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.pose import Pose

if TYPE_CHECKING:
    from ..planner import Planner


class ParkingAction(Action):
    def __init__(self, planner: "Planner", strategy: Strategy, pose: models.Pose):
        super().__init__(f"Parking action at ({int(pose.x)}, {int(pose.y)})", planner, strategy, interruptable=False)
        self.parking_pose = pose
        self.before_action_func = self.before_action
        self.after_action_func = self.after_action
        self.interruptable = False
        self.moving_action: Callable[[], Awaitable[None]] | None = None

    def weight(self) -> float:
        if self.planner.game_context.countdown > 7:
            return 0

        return 9_999_000.0

    async def before_action(self):
        self.logger.info(f"{self.name}: before_action")
        self.planner.pose_order = None
        await self.planner.sio_ns.emit("brake")

        if not self.planner.game_context.front_free and not self.planner.game_context.back_free:
            # Go forward and drop back while moving, final angle 180, then drop front
            direction = MotionDirection.FORWARD_ONLY
            angle = 180.0
            bypass_final_orientation = False
            self.moving_action = self.moving_drop
        elif self.planner.game_context.back_free:
            # Go backward, final angle 180, then drop front
            direction = MotionDirection.BACKWARD_ONLY
            angle = 180.0
            bypass_final_orientation = False
        elif self.planner.game_context.back_free:
            # Go forward, final angle 0, then drop back
            direction = MotionDirection.FORWARD_ONLY
            angle = 0.0
            bypass_final_orientation = False
        else:
            # Go forward or backward, bypass final orientation
            direction = MotionDirection.BIDIRECTIONAL
            angle = 0.0
            bypass_final_orientation = True

        self.pose = Pose(
            x=self.parking_pose.x,
            y=self.parking_pose.y,
            O=angle,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=direction,
            bypass_final_orientation=bypass_final_orientation,
            before_pose_func=self.before_pose,
            after_pose_func=self.after_pose,
        )
        self.poses.append(self.pose)

    async def before_pose(self):
        self.logger.info(f"{self.name}: before_pose")
        if self.moving_action:
            asyncio.create_task(self.moving_action())

    async def after_pose(self):
        self.logger.info(f"{self.name}: after_pose")
        if not self.planner.game_context.front_free:
            duration = await actuators.front_grips_open(self.planner)
            await asyncio.sleep(duration)
            duration = await actuators.front_lift_down(self.planner)
            await asyncio.sleep(duration)
            duration = await actuators.front_arms_open(self.planner)

        if not self.planner.game_context.back_free:
            duration = await actuators.back_grips_open(self.planner)
            await asyncio.sleep(duration)
            duration = await actuators.back_lift_down(self.planner)
            await asyncio.sleep(duration)
            duration = await actuators.back_arms_open(self.planner)

    async def after_action(self):
        self.strategy.clear()

    async def moving_drop(self):
        self.logger.info(f"{self.name}: moving_drop")
        await asyncio.sleep(2.0)
        duration = await actuators.back_grips_open(self.planner)
        await asyncio.sleep(duration)
        duration = await actuators.back_lift_down(self.planner)
        await asyncio.sleep(duration)
        duration = await actuators.back_arms_open(self.planner)
        self.planner.game_context.back_free = True
