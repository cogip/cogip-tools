import asyncio
from typing import TYPE_CHECKING

from cogip import models
from cogip.models.artifacts import FixedObstacleID
from cogip.tools.planner import actuators, logger
from cogip.tools.planner.actions.actions import Action, Actions
from cogip.tools.planner.pose import AdaptedPose
from cogip.tools.planner.table import TableEnum

if TYPE_CHECKING:
    from ..planner import Planner


class ParkingAction(Action):
    def __init__(self, planner: "Planner", actions: Actions, pose: models.Pose):
        super().__init__(f"Parking action at ({int(pose.x)}, {int(pose.y)})", planner, actions, interruptable=False)
        self.after_action_func = self.after_action
        self.actions_backup: Actions = []
        self.interruptable = False

        self.pose = AdaptedPose(
            **pose.model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            allow_reverse=True,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose,
            after_pose_func=self.after_pose,
        )
        self.poses = [self.pose]

    def weight(self) -> float:
        if self.game_context.countdown > 7:
            return 0

        return 9999000.0

    async def before_pose(self):
        logger.info(f"{self.name}: before_pose - tribunes_in_robot={self.game_context.tribunes_in_robot}")
        self.planner.pose_order = None
        await self.planner.sio_ns.emit("brake")
        if self.game_context.properties.table == TableEnum.Game:
            self.game_context.fixed_obstacles[FixedObstacleID.PitArea].enabled = True
            self.game_context.fixed_obstacles[FixedObstacleID.OpponentPitArea].enabled = True
            self.game_context.fixed_obstacles[FixedObstacleID.PamiStartArea].enabled = False

        await asyncio.gather(
            actuators.magnet_center_right_in(self.planner),
            actuators.magnet_center_left_in(self.planner),
            actuators.magnet_side_right_in(self.planner),
            actuators.magnet_side_left_in(self.planner),
        )

        if self.game_context.tribunes_in_robot > 0:
            await actuators.arms_release(self.planner)
            await asyncio.sleep(0.1)

        await actuators.arms_close(self.planner)

        await actuators.lift_140(self.planner)

    async def after_pose(self):
        logger.info(f"{self.name}: after_pose")

    async def after_action(self):
        self.actions.clear()
