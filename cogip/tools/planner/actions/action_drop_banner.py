import asyncio
from typing import TYPE_CHECKING

from cogip.tools.planner import actuators, logger
from cogip.tools.planner.actions.actions import Action, Actions
from cogip.tools.planner.avoidance.avoidance import AvoidanceStrategy
from cogip.tools.planner.pose import Pose

if TYPE_CHECKING:
    from ..planner import Planner


class DropBannerAction(Action):
    """
    Action used to drop the banner on the table border.
    """

    def __init__(
        self,
        planner: "Planner",
        actions: Actions,
        weight: float = 2000000.0,
    ):
        self.custom_weight = weight
        super().__init__("Drop banner action", planner, actions)
        self.before_action_func = self.before_action

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.game_context.avoidance_strategy = new_strategy
        self.planner.shared_properties["avoidance_strategy"] = new_strategy

    async def before_action(self):
        logger.info(f"{self.name}: before_action")
        self.avoidance_backup = self.game_context.avoidance_strategy

        # On start, the robot is facing the back of the table
        self.start_pose = self.pose_current

        # Go in contact of the border
        drop_pose = Pose(
            x=-1000 + 132,
            y=self.start_pose.y,
            O=self.start_pose.O,
            max_speed_linear=10,
            max_speed_angular=10,
            allow_reverse=False,
            bypass_anti_blocking=False,
            timeout_ms=0,
            bypass_final_orientation=False,
            before_pose_func=self.before_drop,
            after_pose_func=self.after_drop,
        )
        self.poses.append(drop_pose)

        # Step back
        step_back_pose = Pose(
            x=-950 + self.game_context.properties.robot_length / 2,
            y=self.start_pose.y,
            O=self.start_pose.O,
            max_speed_linear=50,
            max_speed_angular=50,
            allow_reverse=True,
            bypass_final_orientation=True,
            before_pose_func=self.before_step_back,
            after_pose_func=self.after_step_back,
        )
        self.poses.append(step_back_pose)

    async def before_drop(self):
        logger.info(f"{self.name}: before_drop")
        self.set_avoidance(AvoidanceStrategy.Disabled)
        await asyncio.gather(
            actuators.arm_left_side(self.planner),
            actuators.arm_right_side(self.planner),
            actuators.magnet_center_right_in(self.planner),
            actuators.magnet_center_left_in(self.planner),
            actuators.magnet_side_right_in(self.planner),
            actuators.magnet_side_left_in(self.planner),
        )

    async def after_drop(self):
        logger.info(f"{self.name}: after_drop")
        await actuators.lift_0(self.planner)
        await asyncio.sleep(1)
        self.game_context.score += 20

    async def before_step_back(self):
        logger.info(f"{self.name}: before_step_back")

    async def after_step_back(self):
        logger.info(f"{self.name}: after_step_back")
        self.set_avoidance(self.avoidance_backup)
        await asyncio.gather(
            actuators.arm_left_center(self.planner),
            actuators.arm_right_center(self.planner),
        )

    def weight(self) -> float:
        return self.custom_weight
