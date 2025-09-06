import asyncio
from typing import TYPE_CHECKING

from cogip.models.artifacts import ConstructionAreaID, TribuneID
from cogip.tools.planner import actuators, logger
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.actions.utils import get_relative_pose
from cogip.tools.planner.pose import Pose
from cogip.tools.planner.scservos import SCServoEnum

if TYPE_CHECKING:
    from ..planner import Planner


class BuildTribuneX1Action(Action):
    """
    Action used to build a tribune.
    """

    def __init__(
        self,
        planner: "Planner",
        strategy: Strategy,
        construction_area_id: ConstructionAreaID,
        weight: float = 2000000.0,
    ):
        self.custom_weight = weight
        super().__init__(f"BuildTribuneX1 {construction_area_id.name}", planner, strategy)
        self.before_action_func = self.before_action
        self.construction_area = self.planner.game_context.construction_areas[construction_area_id]
        self.shift_build = 180
        self.shift_approach = self.shift_build + 150
        self.shift_step_back = self.shift_approach

    async def recycle(self):
        self.recycled = True

    async def before_action(self):
        logger.info(f"{self.name}: before_action - tribunes_in_robot={self.planner.game_context.tribunes_in_robot}")
        self.start_pose = self.pose_current

        # Approach
        # Skip approach if the robot is already in front of the construction area
        match self.construction_area.O:
            case 0 | 180:
                diff = abs(self.construction_area.y - self.start_pose.y)
            case -90 | 90:
                diff = abs(self.construction_area.x - self.start_pose.x)
            case _:
                diff = 1000

        if diff >= 5:
            approach_pose = Pose(
                **get_relative_pose(
                    self.construction_area,
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
        else:
            logger.info(f"{self.name}: skip approach (diff = {diff})")
            await self.before_approach()
            await self.after_approach()

        # Build
        build_pose = Pose(
            **get_relative_pose(
                self.construction_area,
                front_offset=self.shift_build,
                angular_offset=180,
            ).model_dump(),
            max_speed_linear=80,
            max_speed_angular=80,
            bypass_final_orientation=False,
            allow_reverse=False,
            after_pose_func=self.after_build,
        )
        self.poses.append(build_pose)

        # Step back
        step_back_pose = Pose(
            **get_relative_pose(
                self.construction_area,
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
        self.poses.append(step_back_pose)

    async def before_approach(self):
        logger.info(f"{self.name}: before_approach")

    async def after_approach(self):
        logger.info(f"{self.name}: after_approach")

    async def after_build(self):
        logger.info(f"{self.name}: after_build - tribunes_in_robot={self.planner.game_context.tribunes_in_robot}")
        if self.planner.game_context.tribunes_in_robot == 2:
            # await actuators.tribune_spread(self.planner)
            await actuators.arm_left_side(self.planner, 1500)
            await actuators.arm_right_side(self.planner, 1500)
            await actuators.magnet_side_left_out(self.planner, 1500)
            await actuators.magnet_side_right_out(self.planner, 1500)
            await asyncio.sleep(0.2)

            await actuators.magnet_center_left_in(self.planner)
            await actuators.magnet_center_right_in(self.planner)
            await asyncio.sleep(0.2)

            await actuators.arms_hold1(self.planner)
            await asyncio.sleep(0.1)

            await actuators.lift_5(self.planner)
            await asyncio.sleep(0.2)
        else:
            await actuators.lift_0(self.planner)
            self.planner.scservos.set(SCServoEnum.ARM_RIGHT, 223)
            self.planner.scservos.set(SCServoEnum.ARM_LEFT, 703)
            await asyncio.sleep(0.2)

            await asyncio.gather(
                actuators.magnet_side_right_in(self.planner),
                actuators.magnet_side_left_in(self.planner),
            )
            await asyncio.sleep(0.2)

            await actuators.arms_hold2(self.planner)
            await asyncio.sleep(0.1)

            await actuators.arms_release(self.planner)
            await asyncio.sleep(0.1)

            await actuators.arms_close(self.planner)
            await asyncio.sleep(0.2)

        self.planner.game_context.tribunes_in_robot -= 1
        self.construction_area.tribune_level += 1

    async def before_step_back(self):
        logger.info(f"{self.name}: before_step_back")

    async def after_step_back(self):
        logger.info(f"{self.name}: after_step_back - tribunes_in_robot={self.planner.game_context.tribunes_in_robot}")
        self.construction_area.enabled = True
        if self.planner.game_context.tribunes_in_robot == 1:
            await asyncio.gather(
                actuators.arm_left_center(self.planner),
                actuators.arm_right_center(self.planner),
                actuators.magnet_side_left_center(self.planner),
                actuators.magnet_side_right_center(self.planner),
                actuators.lift_0(self.planner),
            )
        else:
            await asyncio.gather(
                actuators.arm_left_front(self.planner),
                actuators.arm_right_front(self.planner),
            )
        self.planner.game_context.score += 4

    def weight(self) -> float:
        if self.planner.game_context.tribunes_in_robot == 0 or self.construction_area.tribune_level != 0:
            return 0

        if (
            self.construction_area.id == ConstructionAreaID.LocalBottomSmall
            and self.planner.game_context.tribunes[TribuneID.LocalBottom].enabled
        ):
            return 0

        if (
            self.construction_area.id == ConstructionAreaID.OppositeBottomSmall
            and self.planner.game_context.tribunes[TribuneID.OppositeBottomSide].enabled
        ):
            return 0

        if (
            self.construction_area.id == ConstructionAreaID.LocalBottomLarge1
            and self.planner.game_context.construction_areas[ConstructionAreaID.LocalBottomLarge2].enabled
        ):
            return 0

        if (
            self.construction_area.id == ConstructionAreaID.LocalBottomLarge1
            and self.planner.game_context.construction_areas[ConstructionAreaID.LocalBottomLarge3].enabled
        ):
            return 0

        if (
            self.construction_area.id == ConstructionAreaID.LocalBottomLarge2
            and self.planner.game_context.construction_areas[ConstructionAreaID.LocalBottomLarge3].enabled
        ):
            return 0

        if (
            self.construction_area.id == ConstructionAreaID.OppositeSideLarge1
            and self.planner.game_context.construction_areas[ConstructionAreaID.OppositeSideLarge2].enabled
        ):
            return 0

        if (
            self.construction_area.id == ConstructionAreaID.OppositeSideLarge1
            and self.planner.game_context.construction_areas[ConstructionAreaID.OppositeSideLarge3].enabled
        ):
            return 0

        if (
            self.construction_area.id == ConstructionAreaID.OppositeSideLarge2
            and self.planner.game_context.construction_areas[ConstructionAreaID.OppositeSideLarge3].enabled
        ):
            return 0

        return self.custom_weight
