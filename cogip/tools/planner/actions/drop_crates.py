from typing import TYPE_CHECKING

from cogip.cpp.libraries.models import MotionDirection
from cogip.models.artifacts import Pantry, PantryID
from cogip.tools.planner.actions import crates_utils
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.actions.utils import get_relative_pose
from cogip.tools.planner.pose import Pose

if TYPE_CHECKING:
    from ..planner import Planner


class DropCratesAction(Action):
    """
    Action used to drop crates on pantry.
    """

    def __init__(
        self,
        planner: "Planner",
        strategy: Strategy,
        pantry_id: PantryID,
        weight: float = 2000000.0,
    ):
        self.custom_weight = weight
        super().__init__(f"DropCrates {pantry_id.name}", planner, strategy)
        self.before_action_func = self.before_action
        self.after_action_func = self.after_action
        self.pantry_id = pantry_id
        self.shift_approach = 0
        self.shift_step_back = 90

    @property
    def pantry(self) -> Pantry:
        return self.planner.game_context.pantries[self.pantry_id]

    async def recycle(self):
        self.pantry.enabled = False
        self.recycled = True

    async def before_action(self):
        self.logger.info(f"{self.name}: before_action")
        self.poses.clear()
        self.pantry_enabled_backup = self.pantry.enabled
        self.side = "front" if not self.planner.game_context.front_free else "back"

        # Approach
        x, y = crates_utils.shift_pantry_center_from_border(self.pantry)
        # angle = self.pantry.O
        # if self.side == "back":
        #     angle = (angle + 180) % 360
        approach_pose = Pose(
            x=x,
            y=y,
            # O=angle,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY if self.side == "front" else MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_approach,
            after_pose_func=self.after_approach,
        )
        self.poses.append(approach_pose)
        self.logger.info(f"{self.name}: approach: {approach_pose.pose}")

    async def before_approach(self):
        self.logger.info(f"{self.name}: before_approach")
        self.pantry_enabled_backup = self.pantry.enabled
        self.pantry.enabled = False

    async def after_approach(self):
        self.logger.info(f"{self.name}: after_approach")
        drop_pose = await crates_utils.drop_crates(self.planner, self.side)
        self.before_drop_org = drop_pose.before_pose_func
        self.after_drop_org = drop_pose.after_pose_func
        drop_pose.before_pose_func = self.before_drop
        drop_pose.after_pose_func = self.after_drop
        self.poses.append(drop_pose)

    async def before_drop(self):
        self.logger.info(f"{self.name}: before_drop")
        self.recyclable = False
        await self.before_drop_org()

    async def after_drop(self):
        self.logger.info(f"{self.name}: after_drop")
        await self.after_drop_org()

        # Step back
        pose_current = self.pose_current
        shift_step_back = self.shift_step_back if self.side == "front" else -self.shift_step_back
        step_back_pose = Pose(
            **get_relative_pose(pose_current, front_offset=-shift_step_back).model_dump(),
            max_speed_linear=50,
            max_speed_angular=50,
            motion_direction=MotionDirection.BACKWARD_ONLY if self.side == "front" else MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_step_back,
            after_pose_func=self.after_step_back,
        )
        self.poses.append(step_back_pose)
        self.logger.info(
            f"{self.name}: step back: x={step_back_pose.x: 5.2f} y={step_back_pose.y: 5.2f} O={step_back_pose.O: 3.2f}°"
        )

    async def before_step_back(self):
        self.logger.info(f"{self.name}: before_step_back")

    async def after_step_back(self):
        self.logger.info(f"{self.name}: after_step_back")

    async def after_action(self):
        self.logger.info(f"{self.name}: after_action")
        self.pantry.enabled = True

    def weight(self) -> float:
        if self.planner.game_context.front_free and self.planner.game_context.back_free:
            self.logger.info(f"{self.name}: Rejected: both front and back are free")
            return 0

        if self.pantry.enabled:
            self.logger.info(f"{self.name}: Rejected: pantry already enabled")
            return 0

        return self.custom_weight
