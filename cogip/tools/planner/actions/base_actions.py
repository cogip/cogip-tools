import asyncio
from typing import TYPE_CHECKING

from cogip import models
from cogip.models import artifacts
from cogip.tools.planner.actions.actions import Action, Actions
from cogip.tools.planner.avoidance.avoidance import AvoidanceStrategy
from cogip.tools.planner.camp import Camp
from cogip.tools.planner.pose import AdaptedPose, Pose

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
            O=self.planner.pose_current.angle,
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
            O=self.planner.pose_current.angle,
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
            O=self.planner.pose_current.angle,
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


class GrabTribuneAction(Action):
    """
    Action used to grab tribune using magnets.
    """

    def __init__(self, planner: "Planner", actions: Actions, tribune_id: artifacts.TribuneID):
        super().__init__("GrabTribune action", planner, actions)
        self.before_action_func = self.before_action
        self.tribune = self.game_context.tribunes[tribune_id]
        self.shift_approach = 335
        self.shift_forward = 160

        match self.tribune.O:
            case -90:
                self.approach_x = self.tribune.x
                self.approach_y = -1500 + self.shift_approach
                self.capture_x = self.approach_x
                self.capture_y = self.approach_y - self.shift_forward
            case 90:
                self.approach_x = self.tribune.x
                self.approach_y = 1500 - self.shift_approach
                self.capture_x = self.approach_x
                self.capture_y = self.approach_y + self.shift_forward
            case 180:
                self.approach_x = -1000 + self.shift_approach
                self.approach_y = self.tribune.y
                self.capture_x = self.approach_x - self.shift_forward
                self.capture_y = self.approach_y

    async def recycle(self):
        # await actuators.cart_magnet_off(self.planner)
        # await actuators.cart_in(self.planner)
        self.tribune.enabled = True
        self.recycled = True

    async def before_action(self):
        self.start_pose = models.Pose(
            x=self.planner.pose_current.x,
            y=self.planner.pose_current.y,
            O=self.planner.pose_current.angle,
        )

        pose = Pose(
            x=self.approach_x,
            y=self.approach_y,
            O=self.tribune.O,
            max_speed_linear=66,
            max_speed_angular=66,
            allow_reverse=False,
            before_pose_func=self.before_pose1,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose)

        # Capture
        pose = Pose(
            x=self.capture_x,
            y=self.capture_y,
            O=self.tribune.O,
            max_speed_linear=5,
            max_speed_angular=5,
            allow_reverse=False,
            bypass_anti_blocking=True,
            timeout_ms=3000,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose)

        # Step-back
        pose = Pose(
            x=self.approach_x,
            y=self.approach_y,
            O=self.tribune.O,
            max_speed_linear=10,
            max_speed_angular=10,
            allow_reverse=True,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose)

    async def before_pose1(self):
        # await asyncio.gather(
        #     actuators.bottom_grip_close(self.planner),
        #     actuators.top_grip_close(self.planner),
        # )
        # await asyncio.gather(
        #     actuators.top_lift_up(self.planner),
        #     actuators.bottom_lift_up(self.planner),
        # )
        pass

    async def after_pose1(self):
        # await actuators.cart_out(self.planner)
        # await actuators.cart_magnet_on(self.planner)

        self.tribune.enabled = False

    async def after_pose2(self):
        await asyncio.sleep(1)

    async def after_pose3(self):
        self.tribune.enabled = True
        # if BoolSensorEnum.MAGNET_LEFT in self.game_context.emulated_actuator_states:
        #     self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_LEFT].state = True
        # if BoolSensorEnum.MAGNET_RIGHT in self.game_context.emulated_actuator_states:
        #     self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_RIGHT].state = True

    def weight(self) -> float:
        if not self.tribune.enabled:
            return 0
        # if not (
        #     self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_LEFT].state
        #     and self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_RIGHT].state
        # ):
        #     return 0
        # if (
        #     self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_LEFT].state
        #     or self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_RIGHT].state
        # ):
        #     return 0

        return 2000000.0
