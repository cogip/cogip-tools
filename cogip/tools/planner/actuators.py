import asyncio
from typing import TYPE_CHECKING

from cogip.models.actuators import (
    PositionalActuatorCommand,
    PositionalActuatorEnum,
    ServoCommand,
    ServoEnum,
)
from .scservos import SCServoEnum

if TYPE_CHECKING:
    from cogip.tools.planner.planner import Planner


# Servos
async def servo_command(planner: "Planner", servo: ServoEnum, command: int) -> float:
    await planner.sio_ns.emit("actuator_command", ServoCommand(id=servo, command=command).model_dump())
    return 0


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


async def magnet_side_right_out(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_SIDE_RIGHT, 385)


# ARM_RIGHT
async def arm_right_front(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_RIGHT, 78)


async def arm_right_center(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_RIGHT, 385)


async def arm_right_side(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_RIGHT, 495)


# MAGNET_CENTER_RIGHT
async def magnet_center_right_out(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_CENTER_RIGHT, 255)


async def magnet_center_right_center(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_CENTER_RIGHT, 558)


async def magnet_center_right_in(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_CENTER_RIGHT, 500)  ## TODO


# MAGNET_CENTER_LEFT
async def magnet_center_left_out(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_CENTER_LEFT, 809)


async def magnet_center_left_center(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_CENTER_LEFT, 531)


async def magnet_center_left_in(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_CENTER_LEFT, 500)  ## TODO


# ARM_LEFT
async def arm_left_front(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_LEFT, 923)


async def arm_left_center(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_LEFT, 577)


async def arm_left_side(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_LEFT, 481)


# MAGNET_SIDE_LEFT
async def magnet_side_left_in(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_SIDE_LEFT, 232)


async def magnet_side_left_center(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_SIDE_LEFT, 465)


async def magnet_side_left_out(planner: "Planner"):
    planner.scservos.set(SCServoEnum.MAGNET_SIDE_LEFT, 764)


# ARM_GRIP_LEFT
async def arm_grip_left_open(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_GRIP_LEFT, 356)


async def arm_grip_left_close(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_GRIP_LEFT, 790)


async def arm_grip_left_hold(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_GRIP_LEFT, 286)


# ARM_GRIP_RIGHT
async def arm_grip_right_open(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_GRIP_RIGHT, 882)


async def arm_grip_right_close(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_GRIP_RIGHT, 461)


async def arm_grip_right_hold(planner: "Planner"):
    planner.scservos.set(SCServoEnum.ARM_GRIP_RIGHT, 925)


# GRIP_RIGHT
async def grip_right_open(planner: "Planner"):
    planner.scservos.set(SCServoEnum.GRIP_RIGHT, 212)


async def grip_right_close(planner: "Planner"):
    planner.scservos.set(SCServoEnum.GRIP_RIGHT, 509)


# GRIP_LEFT
async def grip_left_open(planner: "Planner"):
    planner.scservos.set(SCServoEnum.GRIP_LEFT, 206)


async def grip_left_close(planner: "Planner"):
    planner.scservos.set(SCServoEnum.GRIP_LEFT, 527)


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
    await magnet_center_left_center(planner)
    await magnet_center_right_center(planner)


async def arms_open(planner: "Planner"):
    # Left arm first
    await arm_grip_left_open(planner)
    await asyncio.sleep(0.2)

    # Right arm
    await arm_grip_right_open(planner)
    await asyncio.sleep(0.5)

    await grip_left_close(planner)
    await grip_right_close(planner)


async def arms_hold(planner: "Planner"):
    await arm_grip_left_hold(planner)
    await arm_grip_right_hold(planner)


async def arms_release(planner: "Planner"):
    await arm_grip_left_open(planner)
    await arm_grip_right_open(planner)


async def arms_close(planner: "Planner"):
    await grip_left_open(planner)
    await grip_right_open(planner)
    await asyncio.sleep(0.5)

    # Right arm first
    await arm_grip_right_close(planner)

    await asyncio.sleep(0.2)

    # Left arm
    await arm_grip_left_close(planner)
