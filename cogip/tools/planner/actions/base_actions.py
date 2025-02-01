import asyncio
from typing import TYPE_CHECKING

from cogip import models
from cogip.models import artifacts
from cogip.tools.planner import actuators, logger
from cogip.tools.planner.actions.actions import Action, Actions
from cogip.tools.planner.avoidance.avoidance import AvoidanceStrategy
from cogip.tools.planner.camp import Camp
from cogip.tools.planner.pose import AdaptedPose, Pose
from cogip.tools.planner.scservos import SCServoEnum

if TYPE_CHECKING:
    from ..planner import Planner


class AlignAction(Action):
    """
    Action used align the robot before game start.
    """

    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__("Align action", planner, actions)
        self.before_action_func = self.init_poses

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.game_context.avoidance_strategy = new_strategy
        self.planner.shared_properties["avoidance_strategy"] = new_strategy

    async def init_poses(self):
        self.start_pose = models.Pose(
            x=self.planner.pose_current.x,
            y=self.planner.pose_current.y,
            O=self.planner.pose_current.O,
        )
        self.start_avoidance = self.game_context.avoidance_strategy

        if Camp().adapt_y(self.start_pose.y) > 0:
            # Do not do alignment if the robot is in the opposite start position because it is not in a corner
            return

        pose1 = AdaptedPose(
            x=self.start_pose.x,
            y=-1700 + self.game_context.properties.robot_length / 2,
            O=0,
            max_speed_linear=5,
            max_speed_angular=5,
            allow_reverse=True,
            bypass_anti_blocking=True,
            timeout_ms=0,  # TODO
            bypass_final_orientation=True,
            before_pose_func=self.before_pose1,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

    async def before_pose1(self):
        self.set_avoidance(AvoidanceStrategy.Disabled)

    async def after_pose1(self):
        self.set_avoidance(self.start_avoidance)
        current_pose = models.Pose(
            x=self.planner.pose_current.x,
            y=self.planner.pose_current.y,
            O=self.planner.pose_current.O,
        )
        current_pose.y = Camp().adapt_y(-1500 + self.game_context.properties.robot_length / 2)
        current_pose.O = Camp().adapt_angle(90)
        await self.planner.sio_ns.emit("pose_start", current_pose.model_dump())

        pose2 = AdaptedPose(
            x=current_pose.x,
            y=-1250,
            O=180 if current_pose.x > 0 else 0,
            max_speed_linear=20,
            max_speed_angular=20,
            allow_reverse=False,
        )
        self.poses.append(pose2)

        if current_pose.x > 0:
            x = 1200 - self.game_context.properties.robot_length / 2
        else:
            x = -1200 + self.game_context.properties.robot_length / 2
        pose3 = AdaptedPose(
            x=x,
            y=-1250,
            O=0,
            max_speed_linear=5,
            max_speed_angular=5,
            allow_reverse=True,
            bypass_anti_blocking=True,
            timeout_ms=0,  # TODO
            bypass_final_orientation=True,
            before_pose_func=self.before_pose3,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose3)

    async def before_pose3(self):
        self.set_avoidance(AvoidanceStrategy.Disabled)

    async def after_pose3(self):
        self.set_avoidance(self.start_avoidance)
        current_pose = models.Pose(
            x=self.planner.pose_current.x,
            y=self.planner.pose_current.y,
            O=self.planner.pose_current.O,
        )
        if current_pose.x > 0:
            current_pose.x = 1000 - self.game_context.properties.robot_length / 2
        else:
            current_pose.x = -1000 + self.game_context.properties.robot_length / 2
        current_pose.O = 180 if current_pose.x > 0 else 0
        await self.planner.sio_ns.emit("pose_start", current_pose.model_dump())

        pose4 = Pose(
            x=730 if current_pose.x > 0 else -730,
            y=current_pose.y,
            O=current_pose.O,
            max_speed_linear=33,
            max_speed_angular=33,
            allow_reverse=False,
        )
        self.poses.append(pose4)

        pose5 = Pose(
            x=self.start_pose.x,
            y=self.start_pose.y,
            O=self.start_pose.O,
            max_speed_linear=33,
            max_speed_angular=33,
            allow_reverse=True,
        )
        self.poses.append(pose5)

    def weight(self) -> float:
        return 1000000.0


class ParkingAction(Action):
    def __init__(self, planner: "Planner", actions: Actions, pose: models.Pose):
        super().__init__(f"Parking action at ({int(pose.x)}, {int(pose.y)})", planner, actions, interruptable=False)
        self.before_action_func = self.before_action
        self.after_action_func = self.after_action
        self.actions_backup: Actions = []
        self.interruptable = False

        self.pose = AdaptedPose(
            **pose.model_dump(),
            allow_reverse=False,
        )
        self.poses = [self.pose]

    def weight(self) -> float:
        if self.game_context.countdown > 15:
            return 0

        return 9999000.0

    async def before_action(self):
        pass

    async def after_action(self):
        self.game_context.score += 10

        await self.planner.sio_ns.emit("score", self.game_context.score)
        await self.planner.sio_ns.emit("robot_end")
        self.actions.clear()


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
        self.tribune = self.game_context.tribunes[tribune_id]
        self.shift_approach = 280
        self.shift_capture = 160
        self.angle = self.tribune.O

        match self.tribune.O:
            case 0:
                self.approach_x = self.tribune.x + self.shift_approach
                self.approach_y = self.tribune.y
                self.capture_x = self.tribune.x + self.shift_capture
                self.capture_y = self.tribune.y
                self.angle = 180
            case 180:
                self.approach_x = self.tribune.x - self.shift_approach
                self.approach_y = self.tribune.y
                self.capture_x = self.tribune.x - self.shift_capture
                self.capture_y = self.tribune.y
                self.angle = 0
            case -90:
                self.approach_x = self.tribune.x
                self.approach_y = self.tribune.y - self.shift_approach
                self.capture_x = self.tribune.x
                self.capture_y = self.tribune.y - self.shift_capture
                self.angle = 90
            case 90:
                self.approach_x = self.tribune.x
                self.approach_y = self.tribune.y + self.shift_approach
                self.capture_x = self.tribune.x
                self.capture_y = self.tribune.y + self.shift_capture
                self.angle = -90

    async def recycle(self):
        self.tribune.enabled = True
        self.recycled = True

    async def before_action(self):
        self.start_pose = self.planner.pose_current

        # Approach
        pose = Pose(
            x=self.approach_x,
            y=self.approach_y,
            O=self.angle,
            max_speed_linear=100,
            max_speed_angular=60,
            allow_reverse=True,
            before_pose_func=self.before_approach,
            after_pose_func=self.after_approach,
        )
        self.poses.append(pose)

        # Capture
        pose = Pose(
            x=self.capture_x,
            y=self.capture_y,
            O=self.angle,
            max_speed_linear=10,
            max_speed_angular=10,
            allow_reverse=False,
            before_pose_func=self.before_capture,
            after_pose_func=self.after_capture,
        )
        self.poses.append(pose)

    async def before_approach(self):
        logger.info(f"{self.name}: before_approach")
        await actuators.arms_close(self.planner)

    async def after_approach(self):
        logger.info(f"{self.name}: after_approach")
        self.tribune.enabled = False
        await asyncio.sleep(0.2)  # Make sure the obstacle is removed from avoidance

    async def before_capture(self):
        logger.info(f"{self.name}: before_capture")
        await asyncio.gather(
            actuators.tribune_grab(self.planner),
            actuators.arms_open(self.planner),
        )

    async def after_capture(self):
        logger.info(f"{self.name}: after_capture")
        await actuators.arms_hold2(self.planner)
        await asyncio.sleep(0.1)
        self.game_context.tribunes_in_robot = 2

    def weight(self) -> float:
        if not self.tribune.enabled or self.game_context.tribunes_in_robot != 0:
            return 0

        return self.custom_weight


class BuildTribuneX1Action(Action):
    """
    Action used to build a tribune.
    """

    def __init__(
        self,
        planner: "Planner",
        actions: Actions,
        construction_area_id: artifacts.ConstructionAreaID,
        weight: float = 2000000.0,
    ):
        self.custom_weight = weight
        super().__init__(f"BuildTribuneX1 {construction_area_id.name}", planner, actions)
        self.before_action_func = self.before_action
        self.construction_area = self.game_context.construction_areas[construction_area_id]
        self.shift_approach = 335
        self.shift_build = 150

        match self.construction_area.O:
            case 0:
                self.approach_x = self.construction_area.x + self.shift_approach
                self.approach_y = self.construction_area.y
                self.capture_x = self.construction_area.x + self.shift_build
                self.capture_y = self.construction_area.y
                self.angle = 180
            case 180:
                self.approach_x = self.construction_area.x - self.shift_approach
                self.approach_y = self.construction_area.y
                self.capture_x = self.construction_area.x - self.shift_build
                self.capture_y = self.construction_area.y
                self.angle = 0
            case -90:
                self.approach_x = self.construction_area.x
                self.approach_y = self.construction_area.y - self.shift_approach
                self.capture_x = self.construction_area.x
                self.capture_y = self.construction_area.y - self.shift_build
                self.angle = 90
            case 90:
                self.approach_x = self.construction_area.x
                self.approach_y = self.construction_area.y + self.shift_approach
                self.capture_x = self.construction_area.x
                self.capture_y = self.construction_area.y + self.shift_build
                self.angle = -90

    async def recycle(self):
        self.recycled = True

    async def before_action(self):
        logger.info(f"{self.name}: before_action - tribunes_in_robot={self.game_context.tribunes_in_robot}")
        self.start_pose = self.planner.pose_current

        # Approach
        # Skip approach if the robot is already in front of the construction area
        skip_approach = False
        match self.construction_area.O:
            case 0 | 180:
                if self.construction_area.y - self.start_pose.y < 5:
                    skip_approach = True
            case -90 | 90:
                if self.construction_area.x - self.start_pose.x < 5:
                    skip_approach = True

        if not skip_approach:
            pose = Pose(
                x=self.approach_x,
                y=self.approach_y,
                O=self.angle,
                max_speed_linear=80,
                max_speed_angular=60,
                allow_reverse=True,
                before_pose_func=self.before_approach,
                after_pose_func=self.after_approach,
            )
            self.poses.append(pose)
        else:
            await self.before_approach()
            await self.after_approach()

        # Build
        pose = Pose(
            x=self.capture_x,
            y=self.capture_y,
            O=self.angle,
            max_speed_linear=80,
            max_speed_angular=60,
            allow_reverse=False,
            after_pose_func=self.after_build,
        )
        self.poses.append(pose)

        # Step back
        pose = Pose(
            x=self.approach_x,
            y=self.approach_y,
            O=self.angle,
            max_speed_linear=20,
            max_speed_angular=20,
            allow_reverse=True,
            after_pose_func=self.after_step_back,
        )
        self.poses.append(pose)

    async def before_approach(self):
        logger.info(f"{self.name}: before_approach")

    async def after_approach(self):
        logger.info(f"{self.name}: after_approach")

    async def after_build(self):
        logger.info(f"{self.name}: after_build - tribunes_in_robot={self.game_context.tribunes_in_robot}")
        if self.game_context.tribunes_in_robot == 2:
            await actuators.tribune_spread(self.planner)
            await asyncio.sleep(0.2)

            await actuators.arms_hold1(self.planner)
            await asyncio.sleep(0.1)

            await actuators.lift_5(self.planner)
            await asyncio.sleep(0.2)
        else:
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

        self.game_context.tribunes_in_robot -= 1
        self.construction_area.tribune_level += 1

    async def after_step_back(self):
        logger.info(f"{self.name}: after_step_back - tribunes_in_robot={self.game_context.tribunes_in_robot}")
        self.construction_area.enabled = True
        if self.game_context.tribunes_in_robot == 1:
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

    def weight(self) -> float:
        if self.game_context.tribunes_in_robot == 0 or self.construction_area.tribune_level != 0:
            return 0

        return self.custom_weight


class BuildTribuneX2Action(Action):
    """
    Action used to build a 2-story tribune.
    """

    def __init__(
        self,
        planner: "Planner",
        actions: Actions,
        construction_area_id: artifacts.ConstructionAreaID,
        weight: float = 2000000.0,
    ):
        self.custom_weight = weight
        super().__init__(f"BuildTribuneX2 {construction_area_id.name}", planner, actions)
        self.before_action_func = self.before_action
        self.construction_area = self.game_context.construction_areas[construction_area_id]
        self.shift_approach = 335
        self.shift_build = 150

        match self.construction_area.O:
            case 0:
                self.approach_x = self.construction_area.x + self.shift_approach
                self.approach_y = self.construction_area.y
                self.capture_x = self.construction_area.x + self.shift_build
                self.capture_y = self.construction_area.y
                self.angle = 180
            case 180:
                self.approach_x = self.construction_area.x - self.shift_approach
                self.approach_y = self.construction_area.y
                self.capture_x = self.construction_area.x - self.shift_build
                self.capture_y = self.construction_area.y
                self.angle = 0
            case -90:
                self.approach_x = self.construction_area.x
                self.approach_y = self.construction_area.y - self.shift_approach
                self.capture_x = self.construction_area.x
                self.capture_y = self.construction_area.y - self.shift_build
                self.angle = 90
            case 90:
                self.approach_x = self.construction_area.x
                self.approach_y = self.construction_area.y + self.shift_approach
                self.capture_x = self.construction_area.x
                self.capture_y = self.construction_area.y + self.shift_build
                self.angle = -90

    async def recycle(self):
        self.recycled = True

    async def before_action(self):
        logger.info(f"{self.name}: before_action - tribunes_in_robot={self.game_context.tribunes_in_robot}")
        self.start_pose = self.planner.pose_current

        # Approach
        # Skip approach if the robot is already in front of the construction area
        skip_approach = False
        match self.construction_area.O:
            case 0 | 180:
                if self.construction_area.y - self.start_pose.y < 5:
                    skip_approach = True
            case -90 | 90:
                if self.construction_area.x - self.start_pose.x < 5:
                    skip_approach = True

        if not skip_approach:
            pose = Pose(
                x=self.approach_x,
                y=self.approach_y,
                O=self.angle,
                max_speed_linear=80,
                max_speed_angular=60,
                allow_reverse=True,
                before_pose_func=self.before_approach,
                after_pose_func=self.after_approach,
            )
            self.poses.append(pose)
        else:
            await self.before_approach()
            await self.after_approach()

        # Build
        pose = Pose(
            x=self.capture_x,
            y=self.capture_y,
            O=self.angle,
            max_speed_linear=80,
            max_speed_angular=60,
            allow_reverse=False,
            after_pose_func=self.after_build,
        )
        self.poses.append(pose)

        # Step back
        pose = Pose(
            x=self.approach_x,
            y=self.approach_y,
            O=self.angle,
            max_speed_linear=20,
            max_speed_angular=20,
            allow_reverse=True,
            after_pose_func=self.after_step_back,
        )
        self.poses.append(pose)

    async def before_approach(self):
        logger.info(f"{self.name}: before_approach")

    async def after_approach(self):
        logger.info(f"{self.name}: after_approach")

    async def after_build(self):
        logger.info(f"{self.name}: after_build - tribunes_in_robot={self.game_context.tribunes_in_robot}")
        await actuators.tribune_spread(self.planner)
        await asyncio.sleep(0.2)

        await actuators.arms_hold1(self.planner)
        await asyncio.sleep(0.1)

        await actuators.lift_140(self.planner)
        await asyncio.sleep(1)

        self.planner.scservos.set(SCServoEnum.ARM_RIGHT, 223)
        self.planner.scservos.set(SCServoEnum.ARM_LEFT, 703)
        await asyncio.sleep(0.2)

        await asyncio.gather(
            actuators.magnet_side_left_in(self.planner),
            actuators.magnet_side_right_in(self.planner),
        )
        await asyncio.sleep(0.2)

        await actuators.lift_125(self.planner)
        await asyncio.sleep(0.5)

        await actuators.arms_hold2(self.planner)
        await asyncio.sleep(0.1)

        await actuators.arms_release(self.planner)
        await asyncio.sleep(0.1)

        await asyncio.gather(
            actuators.arms_close(self.planner),
            actuators.arm_left_side(self.planner),
            actuators.arm_right_side(self.planner),
        )

        self.game_context.tribunes_in_robot -= 2
        self.construction_area.tribune_level += 2

    async def after_step_back(self):
        logger.info(f"{self.name}: after_step_back - tribunes_in_robot={self.game_context.tribunes_in_robot}")
        self.construction_area.enabled = True
        await asyncio.gather(
            actuators.arm_left_center(self.planner),
            actuators.arm_right_center(self.planner),
            actuators.lift_0(self.planner),
        )

    def weight(self) -> float:
        if self.game_context.tribunes_in_robot < 2 or self.construction_area.tribune_level != 0:
            return 0

        return self.custom_weight


class BuildTribuneX3Action(Action):
    """
    Action used to build a 3-story tribune.
    """

    def __init__(
        self,
        planner: "Planner",
        actions: Actions,
        construction_area_id: artifacts.ConstructionAreaID,
        weight: float = 2000000.0,
    ):
        self.custom_weight = weight
        super().__init__(f"BuildTribuneX3 {construction_area_id.name}", planner, actions)
        self.before_action_func = self.before_action
        self.construction_area = self.game_context.construction_areas[construction_area_id]
        self.shift_approach_x2 = 485
        self.shift_build_x2 = 320
        self.shift_step_back_x2 = 340
        self.shift_approach_x3 = 300
        self.shift_build_x3 = 150
        self.shift_step_back_x3 = 335

        match self.construction_area.O:
            case 0:
                self.approach_x2_x = self.construction_area.x + self.shift_approach_x2
                self.approach_x2_y = self.construction_area.y
                self.build_x2_x = self.construction_area.x + self.shift_build_x2
                self.build_x2_y = self.construction_area.y
                self.step_back_x2_x = self.construction_area.x + self.shift_step_back_x2
                self.step_back_x2_y = self.construction_area.y
                self.approach_x3_x = self.construction_area.x + self.shift_approach_x3
                self.approach_x3_y = self.construction_area.y
                self.build_x3_x = self.construction_area.x + self.shift_build_x3
                self.build_x3_y = self.construction_area.y
                self.step_back_x3_x = self.construction_area.x + self.shift_step_back_x3
                self.step_back_x3_y = self.construction_area.y
                self.angle = 180
            case 180:
                self.approach_x2_x = self.construction_area.x - self.shift_approach_x2
                self.approach_x2_y = self.construction_area.y
                self.build_x2_x = self.construction_area.x - self.shift_build_x2
                self.build_x2_y = self.construction_area.y
                self.step_back_x2_x = self.construction_area.x - self.shift_step_back_x2
                self.step_back_x2_y = self.construction_area.y
                self.approach_x3_x = self.construction_area.x - self.shift_approach_x3
                self.approach_x3_y = self.construction_area.y
                self.build_x3_x = self.construction_area.x - self.shift_build_x3
                self.build_x3_y = self.construction_area.y
                self.step_back_x3_x = self.construction_area.x - self.shift_step_back_x3
                self.step_back_x3_y = self.construction_area.y
                self.angle = 0
            case -90:
                self.approach_x2_x = self.construction_area.x
                self.approach_x2_y = self.construction_area.y - self.shift_approach_x2
                self.build_x2_x = self.construction_area.x
                self.build_x2_y = self.construction_area.y - self.shift_build_x2
                self.step_back_x2_x = self.construction_area.x
                self.step_back_x2_y = self.construction_area.y - self.shift_step_back_x2
                self.approach_x3_x = self.construction_area.x
                self.approach_x3_y = self.construction_area.y - self.shift_approach_x3
                self.build_x3_x = self.construction_area.x
                self.build_x3_y = self.construction_area.y - self.shift_build_x3
                self.step_back_x3_x = self.construction_area.x
                self.step_back_x3_y = self.construction_area.y - self.shift_step_back_x3
                self.angle = 90
            case 90:
                self.approach_x2_x = self.construction_area.x
                self.approach_x2_y = self.construction_area.y + self.shift_approach_x2
                self.build_x2_x = self.construction_area.x
                self.build_x2_y = self.construction_area.y + self.shift_build_x2
                self.step_back_x2_x = self.construction_area.x
                self.step_back_x2_y = self.construction_area.y + self.shift_step_back_x2
                self.approach_x3_x = self.construction_area.x
                self.approach_x3_y = self.construction_area.y + self.shift_approach_x3
                self.build_x3_x = self.construction_area.x
                self.build_x3_y = self.construction_area.y + self.shift_build_x3
                self.step_back_x3_x = self.construction_area.x
                self.step_back_x3_y = self.construction_area.y + self.shift_step_back_x3
                self.angle = -90

    async def recycle(self):
        self.recycled = True

    async def before_action(self):
        logger.info(f"{self.name}: before_action - tribunes_in_robot={self.game_context.tribunes_in_robot}")
        self.start_pose = self.planner.pose_current

        # Approach x2
        # Skip approach if the robot is already in front of the construction area
        skip_approach = False
        match self.construction_area.O:
            case 0 | 180:
                if self.construction_area.y - self.start_pose.y < 5:
                    skip_approach = True
            case -90 | 90:
                if self.construction_area.x - self.start_pose.x < 5:
                    skip_approach = True

        if not skip_approach:
            pose = Pose(
                x=self.approach_x2_x,
                y=self.approach_x2_y,
                O=self.angle,
                # max_speed_linear=20 if self.game_context.tribunes_in_robot == 2 else 80,
                # max_speed_angular=5 if self.game_context.tribunes_in_robot == 2 else 80,
                max_speed_linear=80,
                max_speed_angular=60,
                allow_reverse=True,
                before_pose_func=self.before_approach_x2,
                after_pose_func=self.after_approach_x2,
            )
            self.poses.append(pose)
        else:
            await self.before_approach_x2()
            await self.after_approach_x2()

        # Build x2
        pose = Pose(
            x=self.build_x2_x,
            y=self.build_x2_y,
            O=self.angle,
            max_speed_linear=80,
            max_speed_angular=60,
            allow_reverse=False,
            after_pose_func=self.after_build_x2,
        )
        self.poses.append(pose)

        # Step back x2
        pose = Pose(
            x=self.step_back_x2_x,
            y=self.step_back_x2_y,
            O=self.angle,
            max_speed_linear=20,
            max_speed_angular=20,
            allow_reverse=True,
            before_pose_func=self.before_step_back_x2,
            after_pose_func=self.after_step_back_x2,
        )
        self.poses.append(pose)

        # Approach x3
        pose = Pose(
            x=self.approach_x3_x,
            y=self.approach_x3_y,
            O=self.angle,
            max_speed_linear=10,
            max_speed_angular=10,
            allow_reverse=False,
            before_pose_func=self.before_approach_x3,
            after_pose_func=self.after_approach_x3,
        )
        self.poses.append(pose)

        # Build x3
        pose = Pose(
            x=self.build_x3_x,
            y=self.build_x3_y,
            O=self.angle,
            max_speed_linear=10,
            max_speed_angular=10,
            allow_reverse=False,
            before_pose_func=self.before_build_x3,
            after_pose_func=self.after_build_x3,
        )
        self.poses.append(pose)

        # Step back x3
        pose = Pose(
            x=self.step_back_x3_x,
            y=self.step_back_x3_y,
            O=self.angle,
            max_speed_linear=20,
            max_speed_angular=20,
            allow_reverse=True,
            after_pose_func=self.after_step_back_x3,
        )
        self.poses.append(pose)

    async def before_approach_x2(self):
        logger.info(f"{self.name}: before_approach_x2")

    async def after_approach_x2(self):
        logger.info(f"{self.name}: after_approach_x2")
        self.construction_area.enabled = False

    async def after_build_x2(self):
        logger.info(f"{self.name}: after_build_x2 - tribunes_in_robot={self.game_context.tribunes_in_robot}")
        await actuators.tribune_spread(self.planner)
        await asyncio.sleep(0.2)

        await actuators.arms_hold1(self.planner)
        await asyncio.sleep(0.1)

        await actuators.lift_140(self.planner)
        await asyncio.sleep(1.5)

        self.planner.scservos.set(SCServoEnum.ARM_RIGHT, 223)
        self.planner.scservos.set(SCServoEnum.ARM_LEFT, 703)
        await asyncio.sleep(0.2)

        await asyncio.gather(
            actuators.magnet_side_left_in(self.planner),
            actuators.magnet_side_right_in(self.planner),
        )
        await asyncio.sleep(0.2)

        await actuators.lift_125(self.planner)
        await asyncio.sleep(1)

        await actuators.arms_hold2(self.planner)
        await asyncio.sleep(0.1)

        await actuators.arms_release(self.planner)
        await asyncio.sleep(0.2)

        await asyncio.gather(
            actuators.arms_close(self.planner),
            actuators.arm_left_side(self.planner),
            actuators.arm_right_side(self.planner),
        )
        await asyncio.sleep(1.5)

    async def before_step_back_x2(self):
        logger.info(f"{self.name}: before_step_back_x2")

    async def after_step_back_x2(self):
        logger.info(f"{self.name}: after_step_back_x2")
        await actuators.lift_0(self.planner)
        await asyncio.sleep(1.5)

    async def before_approach_x3(self):
        logger.info(f"{self.name}: before_approach_x3")
        await actuators.tribune_grab(self.planner)

    async def after_approach_x3(self):
        logger.info(f"{self.name}: after_approach_x3")
        await actuators.lift_140(self.planner)
        await asyncio.sleep(1.5)

    async def before_build_x3(self):
        logger.info(f"{self.name}: before_build_x3")

    async def after_build_x3(self):
        logger.info(f"{self.name}: after_build_x3")
        await actuators.lift_125(self.planner)
        await asyncio.sleep(0.2)

        await asyncio.gather(
            actuators.magnet_center_left_in(self.planner),
            actuators.magnet_center_right_in(self.planner),
        )

    async def after_step_back_x3(self):
        logger.info(f"{self.name}: after_step_back - tribunes_in_robot={self.game_context.tribunes_in_robot}")
        self.construction_area.enabled = True
        await asyncio.gather(
            actuators.arm_left_center(self.planner),
            actuators.arm_right_center(self.planner),
            actuators.lift_0(self.planner),
        )
        self.game_context.tribunes_in_robot -= 2
        self.construction_area.tribune_level += 2

    def weight(self) -> float:
        if self.game_context.tribunes_in_robot < 2 or self.construction_area.tribune_level != 1:
            return 0

        return self.custom_weight
