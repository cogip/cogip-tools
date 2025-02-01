import asyncio
from typing import TYPE_CHECKING

from cogip.models.actuators import (
    PositionalActuatorCommand,
    PositionalActuatorEnum,
)
from .scservos import SCServoEnum

if TYPE_CHECKING:
    from cogip.tools.planner.planner import Planner


# Positional Motors
async def positional_motor_command(
    planner: "Planner",
    motor: PositionalActuatorEnum,
    command: int,
) -> float:
    await planner.sio_ns.emit("actuator_command", PositionalActuatorCommand(id=motor, command=command).model_dump())
    return 0


## SC Servos


# MAGNET_SIDE_RIGHT
async def magnet_side_right_in(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_SIDE_RIGHT, 923)


async def magnet_side_right_center(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_SIDE_RIGHT, 662)


async def magnet_side_right_out(planner: "Planner", speed: int = 2400):
    planner.scservos.set(SCServoEnum.MAGNET_SIDE_RIGHT, 298, speed)


# ARM_RIGHT
async def arm_right_front(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_RIGHT, 116)


async def arm_right_center(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_RIGHT, 351)


async def arm_right_side(planner: "Planner", speed: int = 2400):
    planner.scservos.set(SCServoEnum.ARM_RIGHT, 508, speed)


# MAGNET_CENTER_RIGHT
async def magnet_center_right_out(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_CENTER_RIGHT, 259)


async def magnet_center_right_center(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_CENTER_RIGHT, 558)


async def magnet_center_right_in(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_CENTER_RIGHT, 848)


# MAGNET_CENTER_LEFT
async def magnet_center_left_out(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_CENTER_LEFT, 811)


async def magnet_center_left_center(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_CENTER_LEFT, 531)


async def magnet_center_left_in(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_CENTER_LEFT, 244)


# ARM_LEFT
async def arm_left_front(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_LEFT, 875)


async def arm_left_center(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_LEFT, 611)


async def arm_left_side(planner: "Planner", speed: int = 2400):
    planner.scservos.set(SCServoEnum.ARM_LEFT, 457, speed)


# MAGNET_SIDE_LEFT
async def magnet_side_left_in(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_SIDE_LEFT, 232)


async def magnet_side_left_center(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_SIDE_LEFT, 480)


async def magnet_side_left_out(planner: "Planner", speed: int = 2400):
    planner.scservos.set(SCServoEnum.MAGNET_SIDE_LEFT, 837, speed)


# ARM_GRIP_LEFT
async def arm_grip_left_open(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_GRIP_LEFT, 356)


async def arm_grip_left_close(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_GRIP_LEFT, 765)


async def arm_grip_left_hold(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_GRIP_LEFT, 240)


# ARM_GRIP_RIGHT
async def arm_grip_right_open(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_GRIP_RIGHT, 882)


async def arm_grip_right_close(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_GRIP_RIGHT, 470)


async def arm_grip_right_hold(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_GRIP_RIGHT, 993)


# GRIP_RIGHT
async def grip_right_open(planner: "Planner"):
    planner.scservos.set(SCServoEnum.GRIP_RIGHT, 202)


async def grip_right_close1(planner: "Planner"):
    planner.scservos.set(SCServoEnum.GRIP_RIGHT, 632)


async def grip_right_close2(planner: "Planner"):
    planner.scservos.set(SCServoEnum.GRIP_RIGHT, 496)


# GRIP_LEFT
async def grip_left_open(planner: "Planner"):
    planner.scservos.set(SCServoEnum.GRIP_LEFT, 809)


async def grip_left_close1(planner: "Planner"):
    planner.scservos.set(SCServoEnum.GRIP_LEFT, 395)


async def grip_left_close2(planner: "Planner"):
    planner.scservos.set(SCServoEnum.GRIP_LEFT, 512)


## Combined Actions
async def tribune_grab(planner: "Planner"):
    await arm_left_center(planner)
    await arm_right_center(planner)
    await magnet_side_left_center(planner)
    await magnet_side_right_center(planner)
    await magnet_center_left_out(planner)
    await magnet_center_right_out(planner)


async def tribune_spread(planner: "Planner"):
    await arm_left_side(planner)
    await arm_right_side(planner)
    await magnet_side_left_out(planner)
    await magnet_side_right_out(planner)
    await magnet_center_left_in(planner)
    await magnet_center_right_in(planner)


async def arms_open(planner: "Planner"):
    # Left arm first
    await arm_grip_left_open(planner)
    await asyncio.sleep(0.2)

    # Right arm
    await arm_grip_right_open(planner)


async def arms_hold1(planner: "Planner"):
    await grip_left_close1(planner)
    await grip_right_close1(planner)
    await asyncio.sleep(0.1)
    await arm_grip_left_hold(planner)
    await arm_grip_right_hold(planner)


async def arms_hold2(planner: "Planner"):
    await grip_left_close2(planner)
    await grip_right_close2(planner)
    await asyncio.sleep(0.1)
    await arm_grip_left_hold(planner)
    await arm_grip_right_hold(planner)


async def arms_release(planner: "Planner"):
    await arm_grip_left_open(planner)
    await arm_grip_right_open(planner)


async def arms_close(planner: "Planner"):
    await grip_left_open(planner)
    await grip_right_open(planner)
    await asyncio.sleep(0.2)

    # Right arm first
    await arm_grip_right_close(planner)

    await asyncio.sleep(0.2)

    # Left arm
    await arm_grip_left_close(planner)
