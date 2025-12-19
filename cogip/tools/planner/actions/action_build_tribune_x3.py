import asyncio
from typing import TYPE_CHECKING

from cogip.models.artifacts import ConstructionArea, ConstructionAreaID, TribuneID
from cogip.models.models import MotionDirection
from cogip.tools.planner import actuators
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.actions.utils import get_relative_pose
from cogip.tools.planner.avoidance.avoidance import AvoidanceStrategy
from cogip.tools.planner.pose import Pose
from cogip.tools.planner.scservos import SCServoEnum

if TYPE_CHECKING:
    from ..planner import Planner


class BuildTribuneX3Action(Action):
    """
    Action used to build a 3-story tribune.
    """

    def __init__(
        self,
        planner: "Planner",
        strategy: Strategy,
        construction_area_id: ConstructionAreaID,
        weight: float = 2000000.0,
    ):
        self.custom_weight = weight
        super().__init__(f"BuildTribuneX3 {construction_area_id.name}", planner, strategy)
        self.before_action_func = self.before_action
        self.construction_area_id = construction_area_id
        self.shift_build_x3 = 160
        self.shift_build_x2 = self.shift_build_x3 + 160
        self.shift_approach_x2 = self.shift_build_x2 + 130
        self.shift_step_back_x2 = self.shift_build_x2 + 20
        self.shift_approach_x3 = self.shift_build_x2 - 20
        self.shift_step_back_x3 = self.shift_approach_x3

    @property
    def construction_area(self) -> ConstructionArea:
        return self.planner.game_context.construction_areas[self.construction_area_id]

    async def recycle(self):
        self.recycled = True

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def before_action(self):
        self.logger.info(
            f"{self.name}: before_action - tribunes_in_robot={self.planner.game_context.tribunes_in_robot}"
        )
        self.avoidance_backup = AvoidanceStrategy(self.planner.shared_properties.avoidance_strategy)
        self.start_pose = self.pose_current

        # Approach x2
        approach_x2_pose = Pose(
            **get_relative_pose(
                self.construction_area,
                front_offset=self.shift_approach_x2,
                angular_offset=180,
            ).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BIDIRECTIONAL,
            before_pose_func=self.before_approach_x2,
            after_pose_func=self.after_approach_x2,
        )
        self.poses.append(approach_x2_pose)

        # Build x2
        build_x2_pose = Pose(
            **get_relative_pose(
                self.construction_area,
                front_offset=self.shift_build_x2,
                angular_offset=180,
            ).model_dump(),
            max_speed_linear=80,
            max_speed_angular=80,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_build_x2,
            after_pose_func=self.after_build_x2,
        )
        self.poses.append(build_x2_pose)

        # Step back x2
        step_back_x2_pose = Pose(
            **get_relative_pose(
                self.construction_area,
                front_offset=self.shift_step_back_x2,
                angular_offset=180,
            ).model_dump(),
            max_speed_linear=50,
            max_speed_angular=50,
            motion_direction=MotionDirection.BIDIRECTIONAL,
            before_pose_func=self.before_step_back_x2,
            after_pose_func=self.after_step_back_x2,
        )
        self.poses.append(step_back_x2_pose)

        # Approach x3
        approach_x3_pose = Pose(
            **get_relative_pose(
                self.construction_area,
                front_offset=self.shift_approach_x3,
                angular_offset=180,
            ).model_dump(),
            max_speed_linear=20,
            max_speed_angular=20,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_approach_x3,
            after_pose_func=self.after_approach_x3,
        )
        self.poses.append(approach_x3_pose)

        # Build x3
        build_x3_pose = Pose(
            **get_relative_pose(
                self.construction_area,
                front_offset=self.shift_build_x3,
                angular_offset=180,
            ).model_dump(),
            max_speed_linear=20,
            max_speed_angular=20,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_build_x3,
            after_pose_func=self.after_build_x3,
        )
        self.poses.append(build_x3_pose)

        # Step back x3
        step_back_x3_pose = Pose(
            **get_relative_pose(
                self.construction_area,
                front_offset=self.shift_step_back_x3,
                angular_offset=180,
            ).model_dump(),
            max_speed_linear=50,
            max_speed_angular=50,
            bypass_final_orientation=False,
            motion_direction=MotionDirection.BIDIRECTIONAL,
            before_pose_func=self.before_step_back_x3,
            after_pose_func=self.after_step_back_x3,
        )
        self.poses.append(step_back_x3_pose)

    async def before_approach_x2(self):
        self.logger.info(f"{self.name}: before_approach_x2")

    async def after_approach_x2(self):
        self.logger.info(f"{self.name}: after_approach_x2")
        self.construction_area.enabled = False

    async def before_build_x2(self):
        self.logger.info(f"{self.name}: before_build_x2")
        self.set_avoidance(AvoidanceStrategy.Disabled)

    async def after_build_x2(self):
        self.logger.info(
            f"{self.name}: after_build_x2 - tribunes_in_robot={self.planner.game_context.tribunes_in_robot}"
        )
        await actuators.lift_5(self.planner)
        await asyncio.sleep(0.2)

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

        await actuators.lift_140(self.planner)
        await asyncio.sleep(1.2)

        self.planner.scservos.set(SCServoEnum.ARM_RIGHT, 223)
        self.planner.scservos.set(SCServoEnum.ARM_LEFT, 703)
        await asyncio.sleep(0.2)

        await actuators.magnet_side_left_in(self.planner)
        await actuators.magnet_side_right_in(self.planner)
        await asyncio.sleep(0.2)

        await actuators.lift_125(self.planner)
        await asyncio.sleep(0.2)

        await actuators.arms_hold2(self.planner)
        await asyncio.sleep(0.1)

        await actuators.arms_release(self.planner)
        await asyncio.sleep(0.2)

        await actuators.arms_close(self.planner)
        await actuators.arm_left_side(self.planner)
        await actuators.arm_right_side(self.planner)
        await asyncio.sleep(0.5)

    async def before_step_back_x2(self):
        self.logger.info(f"{self.name}: before_step_back_x2")

    async def after_step_back_x2(self):
        self.logger.info(f"{self.name}: after_step_back_x2")
        await actuators.lift_0(self.planner)
        await asyncio.sleep(1)

    async def before_approach_x3(self):
        self.logger.info(f"{self.name}: before_approach_x3")
        await actuators.arm_right_front(self.planner)
        await actuators.arm_left_front(self.planner)
        await actuators.magnet_side_right_in(self.planner)
        await actuators.magnet_side_left_in(self.planner)
        await actuators.magnet_center_left_out(self.planner)
        await actuators.magnet_center_right_out(self.planner)

    async def after_approach_x3(self):
        self.logger.info(f"{self.name}: after_approach_x3")
        await actuators.lift_140(self.planner)
        await asyncio.sleep(1.2)

    async def before_build_x3(self):
        self.logger.info(f"{self.name}: before_build_x3")

    async def after_build_x3(self):
        self.logger.info(f"{self.name}: after_build_x3")
        await actuators.lift_125(self.planner)
        await asyncio.sleep(0.2)

        await actuators.magnet_center_left_in(self.planner)
        await actuators.magnet_center_right_in(self.planner)

    async def before_step_back_x3(self):
        self.logger.info(f"{self.name}: before_step_back_x3")

    async def after_step_back_x3(self):
        self.logger.info(
            f"{self.name}: after_step_back - tribunes_in_robot={self.planner.game_context.tribunes_in_robot}"
        )
        self.construction_area.enabled = True
        await actuators.arm_left_center(self.planner)
        await actuators.arm_right_center(self.planner)
        await actuators.lift_0(self.planner)
        self.planner.game_context.tribunes_in_robot -= 2
        self.construction_area.tribune_level += 2
        self.planner.game_context.score += 24
        self.set_avoidance(self.avoidance_backup)

    def weight(self) -> float:
        if self.planner.game_context.tribunes_in_robot < 2 or self.construction_area.tribune_level != 1:
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
            self.construction_area.id == ConstructionAreaID.LocalBottomLarge3
            and self.planner.game_context.tribunes[TribuneID.LocalCenter].enabled
        ):
            return 0

        if (
            self.construction_area.id == ConstructionAreaID.OppositeSideLarge3
            and self.planner.game_context.tribunes[TribuneID.OppositeCenter].enabled
        ):
            return 0

        return self.custom_weight
