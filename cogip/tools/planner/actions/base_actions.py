import asyncio
import math
from typing import TYPE_CHECKING

from cogip import models
from cogip.models import artifacts
from cogip.models.actuators import BoolSensorEnum
from cogip.tools.planner import actuators, logger
from cogip.tools.planner.actions.actions import Action, Actions
from cogip.tools.planner.avoidance.avoidance import AvoidanceStrategy
from cogip.tools.planner.camp import Camp
from cogip.tools.planner.pose import AdaptedPose, Pose
from cogip.tools.planner.table import TableEnum

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

        await asyncio.gather(
            actuators.bottom_grip_close(self.planner),
            actuators.top_grip_close(self.planner),
            actuators.arm_panel_close(self.planner),
            actuators.cart_in(self.planner),
            asyncio.sleep(0.5),
        )
        await asyncio.gather(
            actuators.bottom_lift_up(self.planner),
            actuators.top_lift_up(self.planner),
        )

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


class GripAction(Action):
    """
    Action used to grip plants.
    """

    def __init__(self, planner: "Planner", actions: Actions, plant_supply_id: artifacts.PlantSupplyID):
        super().__init__("Grip action", planner, actions)
        self.before_action_func = self.before_action
        self.plant_supply = self.game_context.plant_supplies[plant_supply_id]
        self.stop_before_center_1 = 180

    async def recycle(self):
        self.plant_supply.enabled = True
        self.recycled = True

    async def before_action(self):
        # Compute first pose to get plants using bottom grips
        self.plant_supply.enabled = False
        self.start_pose = models.Pose(
            x=self.planner.pose_current.x,
            y=self.planner.pose_current.y,
            O=self.planner.pose_current.angle,
        )
        dist_x = self.plant_supply.x - self.planner.pose_current.x
        dist_y = self.plant_supply.y - self.planner.pose_current.y
        dist = math.hypot(dist_x, dist_y)
        pose = Pose(
            x=self.plant_supply.x - dist_x / dist * self.stop_before_center_1,
            y=self.plant_supply.y - dist_y / dist * self.stop_before_center_1,
            O=0,
            max_speed_linear=30,
            max_speed_angular=30,
            allow_reverse=False,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose1,
            intermediate_pose_func=self.intermediate_pose1,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose)

    async def before_pose1(self):
        await actuators.arm_panel_close(self.planner)
        await actuators.bottom_lift_down(self.planner)
        await asyncio.sleep(0.5)
        await actuators.top_lift_down(self.planner)
        await asyncio.sleep(0.5)
        await asyncio.gather(
            actuators.bottom_grip_open(self.planner),
            actuators.top_grip_open(self.planner),
        )

    async def intermediate_pose1(self):
        # Update first pose to take avoidance into account
        dist_x = self.plant_supply.x - self.planner.pose_current.x
        dist_y = self.plant_supply.y - self.planner.pose_current.y
        dist = math.hypot(dist_x, dist_y)
        self.planner.pose_order.x = self.plant_supply.x - dist_x / dist * self.stop_before_center_1
        self.planner.pose_order.y = self.plant_supply.y - dist_y / dist * self.stop_before_center_1
        self.planner.shared_properties["pose_order"] = self.planner.pose_order.path_pose.model_dump(exclude_unset=True)

    async def after_pose1(self):
        await actuators.top_grip_mid_open(self.planner)
        await asyncio.sleep(0.1)
        await actuators.top_grip_mid(self.planner)
        await asyncio.sleep(0.1)
        await actuators.top_grip_mid_close(self.planner)
        await asyncio.sleep(0.1)
        await actuators.top_grip_close(self.planner)
        await asyncio.sleep(0.1)

        if BoolSensorEnum.TOP_GRIP_LEFT in self.game_context.emulated_actuator_states:
            self.game_context.bool_sensor_states[BoolSensorEnum.TOP_GRIP_LEFT].state = True
        if BoolSensorEnum.TOP_GRIP_RIGHT in self.game_context.emulated_actuator_states:
            self.game_context.bool_sensor_states[BoolSensorEnum.TOP_GRIP_RIGHT].state = True

        # Step back
        back_dist = 100
        diff_x = back_dist * math.cos(math.radians(self.planner.pose_current.angle))
        diff_y = back_dist * math.sin(math.radians(self.planner.pose_current.angle))

        pose = Pose(
            x=self.planner.pose_current.x - diff_x,
            y=self.planner.pose_current.y - diff_y,
            O=0,
            max_speed_linear=66,
            max_speed_angular=66,
            allow_reverse=True,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose)

    async def after_pose2(self):
        await actuators.top_lift_up(self.planner)
        await asyncio.sleep(0.5)

        # Compute pose to get plants using bottom grips
        forward_dist = 220
        diff_x = forward_dist * math.cos(math.radians(self.planner.pose_current.angle))
        diff_y = forward_dist * math.sin(math.radians(self.planner.pose_current.angle))

        pose = Pose(
            x=self.planner.pose_current.x + diff_x,
            y=self.planner.pose_current.y + diff_y,
            O=0,
            max_speed_linear=20,
            max_speed_angular=20,
            allow_reverse=False,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose)

    async def after_pose3(self):
        await actuators.bottom_grip_mid_open(self.planner)
        await asyncio.sleep(0.1)
        await actuators.bottom_grip_mid(self.planner)
        await asyncio.sleep(0.1)
        await actuators.bottom_grip_mid_close(self.planner)
        await asyncio.sleep(0.1)
        await actuators.bottom_grip_close(self.planner)
        await asyncio.sleep(0.1)
        await actuators.bottom_lift_up(self.planner)
        if BoolSensorEnum.BOTTOM_GRIP_LEFT in self.game_context.emulated_actuator_states:
            self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_LEFT].state = True
        if BoolSensorEnum.BOTTOM_GRIP_RIGHT in self.game_context.emulated_actuator_states:
            self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_RIGHT].state = True

        # Step back
        back_dist = 250
        diff_x = back_dist * math.cos(math.radians(self.planner.pose_current.angle))
        diff_y = back_dist * math.sin(math.radians(self.planner.pose_current.angle))

        pose = Pose(
            x=self.planner.pose_current.x - diff_x,
            y=self.planner.pose_current.y - diff_y,
            O=0,
            max_speed_linear=66,
            max_speed_angular=66,
            allow_reverse=True,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose4,
        )
        self.poses.append(pose)

    async def after_pose4(self):
        self.plant_supply.enabled = True

    def weight(self) -> float:
        if (
            self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_LEFT].state
            or self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_RIGHT].state
            or self.game_context.bool_sensor_states[BoolSensorEnum.TOP_GRIP_LEFT].state
            or self.game_context.bool_sensor_states[BoolSensorEnum.TOP_GRIP_RIGHT].state
            or self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_LEFT].state
            or self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_RIGHT].state
        ):
            return 0
        return 1000000.0


class PotCaptureAction(Action):
    """
    Action used to capture pots using magnets.
    """

    def __init__(self, planner: "Planner", actions: Actions, pot_supply_id: artifacts.PotSupplyID):
        super().__init__("PotCapture action", planner, actions)
        self.before_action_func = self.before_action
        self.pot_supply = self.game_context.pot_supplies[pot_supply_id]
        self.shift_approach = 335
        self.shift_forward = 160

        match self.pot_supply.angle:
            case -90:
                self.approach_x = self.pot_supply.x
                self.approach_y = -1500 + self.shift_approach
                self.capture_x = self.approach_x
                self.capture_y = self.approach_y - self.shift_forward
            case 90:
                self.approach_x = self.pot_supply.x
                self.approach_y = 1500 - self.shift_approach
                self.capture_x = self.approach_x
                self.capture_y = self.approach_y + self.shift_forward
            case 180:
                self.approach_x = -1000 + self.shift_approach
                self.approach_y = self.pot_supply.y
                self.capture_x = self.approach_x - self.shift_forward
                self.capture_y = self.approach_y

    async def recycle(self):
        await actuators.cart_magnet_off(self.planner)
        await actuators.cart_in(self.planner)
        self.pot_supply.enabled = True
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
            O=self.pot_supply.angle,
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
            O=self.pot_supply.angle,
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
            O=self.pot_supply.angle,
            max_speed_linear=10,
            max_speed_angular=10,
            allow_reverse=True,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose)

    async def before_pose1(self):
        await asyncio.gather(
            actuators.bottom_grip_close(self.planner),
            actuators.top_grip_close(self.planner),
        )
        await asyncio.gather(
            actuators.top_lift_up(self.planner),
            actuators.bottom_lift_up(self.planner),
        )

    async def after_pose1(self):
        await actuators.cart_out(self.planner)
        await actuators.cart_magnet_on(self.planner)

        self.pot_supply.enabled = False

    async def after_pose2(self):
        await asyncio.sleep(1)

    async def after_pose3(self):
        self.pot_supply.enabled = True
        self.pot_supply.count -= 2
        if BoolSensorEnum.MAGNET_LEFT in self.game_context.emulated_actuator_states:
            self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_LEFT].state = True
        if BoolSensorEnum.MAGNET_RIGHT in self.game_context.emulated_actuator_states:
            self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_RIGHT].state = True

    def weight(self) -> float:
        if self.pot_supply.count < 5:
            return 0
        if not (
            self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_LEFT].state
            and self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_RIGHT].state
        ):
            return 0
        if (
            self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_LEFT].state
            or self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_RIGHT].state
        ):
            return 0

        return 2000000.0


class SolarPanelsAction(Action):
    """
    Activate a solar panel group.
    """

    def __init__(self, planner: "Planner", actions: Actions, solar_panels_id: artifacts.SolarPanelsID):
        super().__init__("SolarPanels action", planner, actions)
        self.solar_panels = self.game_context.solar_panels[solar_panels_id]
        self.before_action_func = self.before_action
        self.shift_x = -215
        self.shift_y = 285

    async def recycle(self):
        await actuators.arm_panel_close(self.planner)
        self.recycled = True

    async def before_action(self):
        self.start_pose = models.Pose(
            x=self.planner.pose_current.x,
            y=self.planner.pose_current.y,
            O=self.planner.pose_current.angle,
        )
        if self.game_context.camp.color == Camp.Colors.yellow:
            self.shift_y = -self.shift_y

        if self.solar_panels.id == artifacts.SolarPanelsID.Shared:
            self.game_context.pot_supplies[artifacts.PotSupplyID.LocalBottom].enabled = False
            self.game_context.pot_supplies[artifacts.PotSupplyID.LocalBottom].count = 0
            await asyncio.sleep(0.5)

        # Start pose
        self.pose1 = Pose(
            x=self.solar_panels.x - self.shift_x,
            y=self.solar_panels.y - self.shift_y,
            O=90,
            max_speed_linear=66,
            max_speed_angular=66,
            allow_reverse=True,
            after_pose_func=self.after_pose1,
        )

        self.poses.append(self.pose1)

        # End pose
        self.poses.append(
            Pose(
                x=self.solar_panels.x - self.shift_x,
                y=self.solar_panels.y + self.shift_y,
                O=90,
                max_speed_linear=66,
                max_speed_angular=66,
                allow_reverse=True,
                after_pose_func=self.after_pose2,
            )
        )

        if self.solar_panels.id == artifacts.SolarPanelsID.Shared:
            # Go back to pose1
            self.poses.append(
                Pose(
                    x=self.pose1.x,
                    y=self.pose1.y,
                    O=self.pose1.O,
                    max_speed_linear=66,
                    max_speed_angular=66,
                    allow_reverse=True,
                )
            )

    async def after_pose1(self):
        await actuators.arm_panel_open(self.planner)
        await asyncio.sleep(1)

    async def after_pose2(self):
        await actuators.arm_panel_close(self.planner)
        await asyncio.sleep(0.5)
        self.game_context.score += 15

    def weight(self) -> float:
        return 2000000.0


class PushPotAction(Action):
    """
    push pot in front of a planter.
    """

    def __init__(self, planner: "Planner", actions: Actions, pot_supply_id: artifacts.PotSupplyID):
        super().__init__("PushPot action", planner, actions)
        self.pot_supply = self.game_context.pot_supplies[pot_supply_id]
        self.after_action_func = self.after_action
        self.half_robot_length = self.game_context.properties.robot_length / 2
        margin_x = 160
        margin_y = 50

        match pot_supply_id:
            case artifacts.PotSupplyID.LocalMiddle:
                approach_x = self.pot_supply.x - margin_x - self.half_robot_length
                approach_y = push_y = -1500 + margin_y + self.half_robot_length
                approach_angle = push_angle = 180
                push_x = approach_x + margin_x * 2 + 30
            case artifacts.PotSupplyID.LocalTop:
                approach_x = self.pot_supply.x + margin_x + self.half_robot_length
                approach_y = push_y = -1500 + margin_y + self.half_robot_length
                approach_angle = push_angle = 0
                push_x = approach_x - margin_x * 2 - 30
            case _:
                logger.warning(f"PushPot not available for pot supply {pot_supply_id}")
                return

        self.poses.append(
            AdaptedPose(
                x=approach_x,
                y=approach_y,
                O=approach_angle,
                max_speed_linear=66,
                max_speed_angular=66,
                allow_reverse=True,
            )
        )

        self.poses.append(
            AdaptedPose(
                x=push_x,
                y=push_y,
                O=push_angle,
                max_speed_linear=10,
                max_speed_angular=10,
                allow_reverse=True,
                bypass_final_orientation=True,
                before_pose_func=self.before_pose2,
            )
        )

    async def before_pose2(self):
        self.pot_supply.enabled = False

    async def after_action(self):
        self.pot_supply.count = 0

    async def recycle(self):
        if self.game_context.countdown > 15:
            self.pot_supply.enabled = True
        self.recycled = True

    def weight(self) -> float:
        return 9000000.0


class DropInDropoffZoneAction(Action):
    """
    Drop plants from the lower grips in a dropoff zone.
    """

    def __init__(self, planner: "Planner", actions: Actions, dropoff_zone_id: artifacts.DropoffZoneID, slot: int):
        super().__init__("DropInDropoffZone action", planner, actions)
        self.dropoff_zone = self.game_context.dropoff_zones[dropoff_zone_id]
        self.slot = slot
        self.push_pot: PushPotAction | None = None
        self.after_action_func = self.after_action

        match dropoff_zone_id:
            case artifacts.DropoffZoneID.Top:
                x = self.dropoff_zone.x + (self.slot - 1) * 125 - self.game_context.properties.robot_length / 2
                y = -1180
                if self.slot == 2:
                    # Prepare PushPot action
                    self.push_pot = PushPotAction(self.planner, self.actions, artifacts.PotSupplyID.LocalTop)
                    x2 = self.push_pot.poses[0].x
                    y2 = self.push_pot.poses[0].y
                else:
                    x2 = x - 150
                    y2 = y
                angle = 0
            case artifacts.DropoffZoneID.Bottom:
                x = self.dropoff_zone.x - (self.slot - 1) * 125 + self.game_context.properties.robot_length / 2
                y = -1180
                if self.slot == 2 and self.game_context._table == TableEnum.Training:
                    # Prepare PushPot action
                    self.push_pot = PushPotAction(self.planner, self.actions, artifacts.PotSupplyID.LocalMiddle)
                    x2 = self.push_pot.poses[0].x
                    y2 = self.push_pot.poses[0].y
                else:
                    x2 = x + 150
                    y2 = y
                angle = 180
            case artifacts.DropoffZoneID.Opposite:
                x = x2 = self.dropoff_zone.x
                y = self.dropoff_zone.y + (self.slot - 1) * 125 - self.game_context.properties.robot_length / 2
                y2 = y - 150
                angle = 90

        self.poses.append(
            AdaptedPose(
                x=x,
                y=y,
                O=angle,
                max_speed_linear=66,
                max_speed_angular=66,
                allow_reverse=False,
                after_pose_func=self.after_pose1,
            )
        )

        self.poses.append(
            AdaptedPose(
                x=x2,
                y=y2,
                O=angle,
                max_speed_linear=66,
                max_speed_angular=66,
                allow_reverse=True,
                after_pose_func=self.after_pose2,
            )
        )

    async def after_pose1(self):
        if (
            self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_LEFT].state
            and self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_LEFT].state
        ):
            # Do not count plant without pot because we do not know its color
            self.game_context.score += 3  # Plant valid
            self.game_context.score += 1  # Plant in pot

        if (
            self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_RIGHT].state
            and self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_RIGHT].state
        ):
            # Do not count plant without pot because we do not know its color
            self.game_context.score += 3  # Plant valid
            self.game_context.score += 1  # Plant in pot

        await actuators.bottom_grip_open(self.planner)
        await actuators.cart_magnet_off(self.planner)
        await asyncio.sleep(0.1)
        await actuators.cart_in(self.planner)

    async def after_pose2(self):
        self.dropoff_zone.free_slots -= 1
        if BoolSensorEnum.BOTTOM_GRIP_LEFT in self.game_context.emulated_actuator_states:
            self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_LEFT].state = False
        if BoolSensorEnum.MAGNET_RIGHT in self.game_context.emulated_actuator_states:
            self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_RIGHT].state = False
        if BoolSensorEnum.MAGNET_LEFT in self.game_context.emulated_actuator_states:
            self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_LEFT].state = False
        if BoolSensorEnum.BOTTOM_GRIP_RIGHT in self.game_context.emulated_actuator_states:
            self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_RIGHT].state = False

    async def after_action(self):
        if self.push_pot:
            self.actions.append(self.push_pot)

    def weight(self) -> float:
        if not (
            self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_LEFT].state
            and self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_RIGHT].state
        ):
            return 0

        if self.slot + 1 == self.dropoff_zone.free_slots:
            return 1000000.0
        return 0


class DropInPlanterAction(Action):
    """
    Drop plants from the upper grips in a planter.
    """

    def __init__(self, planner: "Planner", actions: Actions, planter_id: artifacts.PlanterID):
        super().__init__("DropInPlanter action", planner, actions)
        self.planter = self.game_context.planters[planter_id]
        self.blocking_extra_move = 20
        self.front_excess = 85
        self.approach_delta = 50
        self.half_robot_length = self.game_context.properties.robot_length / 2

        if self.game_context.camp.color == Camp.Colors.blue:
            match planter_id:
                case artifacts.PlanterID.Top:
                    drop_x = self.planter.x + self.front_excess + self.blocking_extra_move - self.half_robot_length
                    approach_x = self.planter.x - self.approach_delta - self.half_robot_length
                    approach_y = drop_y = self.planter.y
                case artifacts.PlanterID.LocalSide | artifacts.PlanterID.Test:
                    approach_x = drop_x = self.planter.x
                    drop_y = self.planter.y - self.front_excess - self.blocking_extra_move + self.half_robot_length
                    approach_y = self.planter.y + self.approach_delta + self.half_robot_length
                case artifacts.PlanterID.OppositeSide:
                    approach_x = drop_x = self.planter.x
                    drop_y = self.planter.y + self.front_excess + self.blocking_extra_move - self.half_robot_length
                    approach_y = self.planter.y - self.approach_delta - self.half_robot_length
        else:
            match planter_id:
                case artifacts.PlanterID.Top:
                    drop_x = self.planter.x + self.front_excess + self.blocking_extra_move - self.half_robot_length
                    approach_x = self.planter.x - self.approach_delta - self.half_robot_length
                    approach_y = drop_y = self.planter.y
                case artifacts.PlanterID.LocalSide | artifacts.PlanterID.Test:
                    approach_x = drop_x = self.planter.x
                    drop_y = self.planter.y + self.front_excess + self.blocking_extra_move - self.half_robot_length
                    approach_y = self.planter.y - self.approach_delta - self.half_robot_length
                case artifacts.PlanterID.OppositeSide:
                    approach_x = drop_x = self.planter.x
                    drop_y = self.planter.y - self.front_excess - self.blocking_extra_move + self.half_robot_length
                    approach_y = self.planter.y + self.approach_delta + self.half_robot_length

        self.poses.append(
            Pose(
                x=approach_x,
                y=approach_y,
                O=self.planter.O,
                max_speed_linear=66,
                max_speed_angular=66,
                allow_reverse=False,
                before_pose_func=self.before_pose1,
            )
        )

        self.poses.append(
            Pose(
                x=drop_x,
                y=drop_y,
                O=self.planter.O,
                max_speed_linear=5,
                max_speed_angular=5,
                allow_reverse=False,
                bypass_anti_blocking=True,
                timeout_ms=0,  # TODO
                before_pose_func=self.before_pose2,
                after_pose_func=self.after_pose2,
            )
        )

        self.poses.append(
            Pose(
                x=approach_x,
                y=approach_y,
                O=self.planter.O,
                max_speed_linear=66,
                max_speed_angular=66,
                allow_reverse=True,
            )
        )

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.game_context.avoidance_strategy = new_strategy
        self.planner.shared_properties["avoidance_strategy"] = new_strategy

    async def before_pose1(self):
        self.start_pose = models.Pose(
            x=self.planner.pose_current.x,
            y=self.planner.pose_current.y,
            O=self.planner.pose_current.angle,
        )
        self.start_avoidance = self.game_context.avoidance_strategy
        match self.planter.id:
            case artifacts.PlanterID.LocalSide:
                self.game_context.pot_supplies[artifacts.PotSupplyID.LocalTop].enabled = False
            case artifacts.PlanterID.Test:
                self.game_context.pot_supplies[artifacts.PotSupplyID.LocalMiddle].enabled = False
            case artifacts.PlanterID.OppositeSide:
                self.game_context.pot_supplies[artifacts.PotSupplyID.OppositeMiddle].enabled = False

    async def before_pose2(self):
        self.set_avoidance(AvoidanceStrategy.Disabled)
        await actuators.bottom_grip_mid_close(self.planner)

    async def after_pose2(self):
        self.set_avoidance(self.start_avoidance)

        if self.game_context.bool_sensor_states[BoolSensorEnum.TOP_GRIP_LEFT].state:
            self.game_context.score += 3  # Plant valid
            self.game_context.score += 1  # Plant in planter
        if self.game_context.bool_sensor_states[BoolSensorEnum.TOP_GRIP_RIGHT].state:
            self.game_context.score += 3  # Plant valid
            self.game_context.score += 1  # Plant in planter

        await actuators.top_lift_mid(self.planner)
        await asyncio.sleep(0.7)
        await actuators.top_grip_open(self.planner)
        await asyncio.sleep(0.5)
        await actuators.bottom_grip_mid_open(self.planner)
        await asyncio.sleep(0.1)
        await actuators.bottom_grip_open(self.planner)

        if self.planner.virtual:
            current_pose = models.Pose(
                x=self.planner.pose_current.x,
                y=self.planner.pose_current.y,
                O=self.planner.pose_current.angle,
            )
            if self.game_context.camp.color == Camp.Colors.blue:
                match self.planter.id:
                    case artifacts.PlanterID.Top:
                        current_pose.x = self.planter.x - self.half_robot_length
                    case artifacts.PlanterID.LocalSide | artifacts.PlanterID.Test:
                        current_pose.y = self.planter.y + self.half_robot_length
                    case artifacts.PlanterID.OppositeSide:
                        current_pose.y = self.planter.y - self.half_robot_length
            else:
                match self.planter.id:
                    case artifacts.PlanterID.Top:
                        current_pose.x = self.planter.x - self.half_robot_length
                    case artifacts.PlanterID.LocalSide | artifacts.PlanterID.Test:
                        current_pose.y = self.planter.y - self.half_robot_length
                    case artifacts.PlanterID.OppositeSide:
                        current_pose.y = self.planter.y + self.half_robot_length

            current_pose.O = self.planter.O
            await self.planner.sio_ns.emit("pose_start", current_pose.model_dump())

        if BoolSensorEnum.TOP_GRIP_LEFT in self.game_context.emulated_actuator_states:
            self.game_context.bool_sensor_states[BoolSensorEnum.TOP_GRIP_LEFT].state = False
        if BoolSensorEnum.TOP_GRIP_RIGHT in self.game_context.emulated_actuator_states:
            self.game_context.bool_sensor_states[BoolSensorEnum.TOP_GRIP_RIGHT].state = False

    def weight(self) -> float:
        if (
            self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_LEFT].state
            or self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_RIGHT].state
        ):
            return 0
        if not (
            self.game_context.bool_sensor_states[BoolSensorEnum.TOP_GRIP_LEFT].state
            and self.game_context.bool_sensor_states[BoolSensorEnum.TOP_GRIP_RIGHT].state
        ):
            return 0
        if (
            self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_LEFT].state
            or self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_RIGHT].state
        ):
            return 0
        match self.planter.id:
            case artifacts.PlanterID.LocalSide:
                if self.game_context.pot_supplies[artifacts.PotSupplyID.LocalTop].count > 0:
                    return 0
            case artifacts.PlanterID.OppositeSide:
                if self.game_context.pot_supplies[artifacts.PotSupplyID.OppositeMiddle].count > 0:
                    return 0

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
        await actuators.bottom_grip_close(self.planner)
        await actuators.top_grip_close(self.planner)

        await actuators.cart_in(self.planner)
        await asyncio.sleep(0.1)
        await actuators.bottom_lift_down(self.planner)
        await actuators.top_lift_down(self.planner)
        await asyncio.sleep(0.5)

        for _, plant_supply in self.game_context.plant_supplies.items():
            plant_supply.enabled = False
        for _, pot_supply in self.game_context.pot_supplies.items():
            pot_supply.enabled = False

    async def after_action(self):
        self.game_context.score += 10

        await actuators.top_grip_open(self.planner)
        await asyncio.sleep(0.5)
        await actuators.bottom_grip_mid_open(self.planner)
        await asyncio.sleep(0.1)
        await actuators.bottom_grip_open(self.planner)

        await self.planner.sio_ns.emit("score", self.game_context.score)
        await self.planner.sio_ns.emit("robot_end")
        self.actions.clear()
