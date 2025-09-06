import asyncio
from typing import TYPE_CHECKING

from cogip.models import artifacts
from cogip.tools.planner import actuators, logger
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.actions import Actions, get_relative_pose
from cogip.tools.planner.pose import Pose
from cogip.tools.planner.table import TableEnum

if TYPE_CHECKING:
    from ..planner import Planner


class CaptureTribuneAction(Action):
    """
    Action used to capture tribune using magnets.
    """

    def __init__(
        self,
        planner: "Planner",
        actions: Actions,
        tribune_id: artifacts.TribuneID,
        weight: float = 2000000.0,
    ):
        self.custom_weight = weight
        super().__init__(f"CaptureTribune {tribune_id.name}", planner, actions)
        self.before_action_func = self.before_action
        self.tribune = self.planner.game_context.tribunes[tribune_id]
        self.shift_capture = 140
        self.shift_approach = self.shift_capture + 150
        self.shift_step_back = self.shift_capture + 80

    async def recycle(self):
        self.tribune.enabled = True
        self.recycled = True

    async def before_action(self):
        self.start_pose = self.pose_current

        # Approach
        approach_pose = Pose(
            **get_relative_pose(
                self.tribune,
                front_offset=self.shift_approach,
                angular_offset=180,
            ).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            allow_reverse=True,
            before_pose_func=self.before_approach,
            after_pose_func=self.after_approach,
        )
        self.poses.append(approach_pose)

        # Capture
        capture_pose = Pose(
            **get_relative_pose(
                self.tribune,
                front_offset=self.shift_capture,
                angular_offset=180,
            ).model_dump(),
            max_speed_linear=20,
            max_speed_angular=20,
            allow_reverse=False,
            bypass_final_orientation=False,
            before_pose_func=self.before_capture,
            after_pose_func=self.after_capture,
        )
        self.poses.append(capture_pose)

        if (
            (
                self.tribune.id == artifacts.TribuneID.LocalCenter
                and self.planner.shared_properties.table == TableEnum.Training
            )
            or self.tribune.id == artifacts.TribuneID.LocalTop
            or self.tribune.id == artifacts.TribuneID.LocalTopSide
            or self.tribune.id == artifacts.TribuneID.LocalBottomSide
            or self.tribune.id == artifacts.TribuneID.OppositeTop
            or self.tribune.id == artifacts.TribuneID.OppositeTopSide
            or self.tribune.id == artifacts.TribuneID.OppositeBottomSide
        ):
            # Step back
            pose = Pose(
                **get_relative_pose(
                    self.tribune,
                    front_offset=self.shift_step_back,
                    angular_offset=180,
                ).model_dump(),
                max_speed_linear=50,
                max_speed_angular=50,
                allow_reverse=True,
                bypass_final_orientation=False,
                before_pose_func=self.before_step_back,
                after_pose_func=self.after_step_back,
            )
            self.poses.append(pose)

    async def before_approach(self):
        logger.info(f"{self.name}: before_approach")
        await actuators.arms_close(self.planner)

    async def after_approach(self):
        logger.info(f"{self.name}: after_approach")

    async def before_capture(self):
        logger.info(f"{self.name}: before_capture")
        self.tribune.enabled = False
        await actuators.lift_0(self.planner)
        await asyncio.gather(
            actuators.tribune_grab(self.planner),
            actuators.arms_open(self.planner),
        )
        await asyncio.sleep(0.2)  # Make sure the obstacle is removed from avoidance

    async def after_capture(self):
        logger.info(f"{self.name}: after_capture")
        await actuators.arms_hold2(self.planner)
        await asyncio.sleep(0.1)
        self.planner.game_context.tribunes_in_robot = 2

    async def before_step_back(self):
        logger.info(f"{self.name}: before_step_back")

    async def after_step_back(self):
        logger.info(f"{self.name}: after_step_back")

    def weight(self) -> float:
        if not self.tribune.enabled or self.planner.game_context.tribunes_in_robot != 0:
            return 0

        return self.custom_weight
