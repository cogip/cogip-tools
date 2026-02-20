from typing import TYPE_CHECKING

from cogip.models.actuators import (
    PositionalActuatorCommand,
    PositionalActuatorEnum,
)
from .scservos import SCServoEnum

if TYPE_CHECKING:
    from cogip.tools.planner.planner import Planner

# Lift positions
LIFT_DOWN = 0
LIFT_MID = 80
LIFT_UP = 125

# Duration of actuator movements is seconds
GRIP_MOVE_DURATION_SEC = 0.5
AXIS_MOVE_DURATION_SEC = 0.5
ARM_MOVE_DURATION_SEC = 0.5
LIFT_MOVE_DURATION_SEC = 1.0
SCISSOR_MOVE_DURATION_SEC = 0.5

# Define center and offset for servos positions
FRONT_GRIP_LEFT_SIDE_ZERO = 592
FRONT_GRIP_LEFT_CENTER_ZERO = 579
FRONT_GRIP_RIGHT_CENTER_ZERO = 606
FRONT_GRIP_RIGHT_SIDE_ZERO = 580
FRONT_AXIS_LEFT_SIDE_ZERO = 554
FRONT_AXIS_LEFT_CENTER_ZERO = 531
FRONT_AXIS_RIGHT_CENTER_ZERO = 551
FRONT_AXIS_RIGHT_SIDE_ZERO = 523
FRONT_ARM_LEFT_ZERO = 373
FRONT_ARM_RIGHT_ZERO = 321
FRONT_SCISSOR_LEFT_ZERO = 0
FRONT_SCISSOR_RIGHT_ZERO = 0

BACK_GRIP_LEFT_SIDE_ZERO = 0
BACK_GRIP_LEFT_CENTER_ZERO = 0
BACK_GRIP_RIGHT_CENTER_ZERO = 0
BACK_GRIP_RIGHT_SIDE_ZERO = 0
BACK_AXIS_LEFT_SIDE_ZERO = 0
BACK_AXIS_LEFT_CENTER_ZERO = 0
BACK_AXIS_RIGHT_CENTER_ZERO = 0
BACK_AXIS_RIGHT_SIDE_ZERO = 0
BACK_ARM_LEFT_ZERO = 349
BACK_ARM_RIGHT_ZERO = 310
BACK_SCISSOR_LEFT_ZERO = 0
BACK_SCISSOR_RIGHT_ZERO = 0

GRIP_OFFSET_OPEN = 50
GRIP_OFFSET_CLOSE = -21
AXIS_OFFSET_OUT = 0
AXIS_OFFSET_IN = 160
ARM_OFFSET_OPEN = 393
ARM_OFFSET_CLOSE = -20
SCISSOR_OFFSET_OPEN = 0
SCISSOR_OFFSET_CLOSE = 0


async def actuators_init(planner: "Planner"):
    """
    Send actuators initialization command to the firmware.
    """
    await planner.sio_ns.emit("actuator_init")
    await front_arms_close(planner)
    await back_arms_close(planner)


# Positional Motors
async def positional_motor_command(
    planner: "Planner",
    motor: PositionalActuatorEnum,
    command: int,
    speed: int = 100,
    timeout: int = 2000,
) -> float:
    await planner.sio_ns.emit(
        "actuator_command",
        PositionalActuatorCommand(
            id=motor,
            command=command,
            speed=speed,
            timeout=timeout,
        ).model_dump(),
    )
    return 0


async def front_lift_down(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.FRONT_LIFT, LIFT_DOWN, speed)
    await planner.sio_ns.emit("lift", (PositionalActuatorEnum.FRONT_LIFT, LIFT_DOWN))
    return LIFT_MOVE_DURATION_SEC


async def front_lift_mid(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.FRONT_LIFT, LIFT_MID, speed, 5000)
    await planner.sio_ns.emit("lift", (PositionalActuatorEnum.FRONT_LIFT, LIFT_MID))
    return LIFT_MOVE_DURATION_SEC / 2


async def front_lift_up(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.FRONT_LIFT, LIFT_UP, speed, 5000)
    await planner.sio_ns.emit("lift", (PositionalActuatorEnum.FRONT_LIFT, LIFT_UP))
    return LIFT_MOVE_DURATION_SEC


async def back_lift_down(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.BACK_LIFT, LIFT_DOWN, speed)
    await planner.sio_ns.emit("lift", (PositionalActuatorEnum.BACK_LIFT, LIFT_DOWN))
    return LIFT_MOVE_DURATION_SEC


async def back_lift_mid(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.BACK_LIFT, LIFT_MID, speed)
    await planner.sio_ns.emit("lift", (PositionalActuatorEnum.BACK_LIFT, LIFT_MID))
    return LIFT_MOVE_DURATION_SEC / 2


async def back_lift_up(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.BACK_LIFT, LIFT_UP, speed)
    await planner.sio_ns.emit("lift", (PositionalActuatorEnum.BACK_LIFT, LIFT_UP))
    return LIFT_MOVE_DURATION_SEC


# SC Servos - Front


## FRONT_GRIP_LEFT_SIDE
async def front_grip_left_side_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_GRIP_LEFT_SIDE, FRONT_GRIP_LEFT_SIDE_ZERO + GRIP_OFFSET_OPEN, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_GRIP_LEFT_SIDE, 1))
    return GRIP_MOVE_DURATION_SEC


async def front_grip_left_side_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_GRIP_LEFT_SIDE, FRONT_GRIP_LEFT_SIDE_ZERO + GRIP_OFFSET_CLOSE, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_GRIP_LEFT_SIDE, 0))
    return GRIP_MOVE_DURATION_SEC


## FRONT_GRIP_LEFT_CENTER
async def front_grip_left_center_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_GRIP_LEFT_CENTER, FRONT_GRIP_LEFT_CENTER_ZERO + GRIP_OFFSET_OPEN, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_GRIP_LEFT_CENTER, 1))
    return GRIP_MOVE_DURATION_SEC


async def front_grip_left_center_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_GRIP_LEFT_CENTER, FRONT_GRIP_LEFT_CENTER_ZERO + GRIP_OFFSET_CLOSE, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_GRIP_LEFT_CENTER, 0))
    return GRIP_MOVE_DURATION_SEC


## FRONT_GRIP_RIGHT_CENTER
async def front_grip_right_center_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_GRIP_RIGHT_CENTER, FRONT_GRIP_RIGHT_CENTER_ZERO + GRIP_OFFSET_OPEN, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_GRIP_RIGHT_CENTER, 1))
    return GRIP_MOVE_DURATION_SEC


async def front_grip_right_center_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_GRIP_RIGHT_CENTER, FRONT_GRIP_RIGHT_CENTER_ZERO + GRIP_OFFSET_CLOSE, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_GRIP_RIGHT_CENTER, 0))
    return GRIP_MOVE_DURATION_SEC


## FRONT_GRIP_RIGHT_SIDE
async def front_grip_right_side_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_GRIP_RIGHT_SIDE, FRONT_GRIP_RIGHT_SIDE_ZERO + GRIP_OFFSET_OPEN, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_GRIP_RIGHT_SIDE, 1))
    return GRIP_MOVE_DURATION_SEC


async def front_grip_right_side_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_GRIP_RIGHT_SIDE, FRONT_GRIP_RIGHT_SIDE_ZERO + GRIP_OFFSET_CLOSE, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_GRIP_RIGHT_SIDE, 0))
    return GRIP_MOVE_DURATION_SEC


## FRONT_AXIS_LEFT_SIDE
async def front_axis_left_side_out(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_AXIS_LEFT_SIDE, FRONT_AXIS_LEFT_SIDE_ZERO + AXIS_OFFSET_OUT, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_AXIS_LEFT_SIDE, 1))
    return AXIS_MOVE_DURATION_SEC


async def front_axis_left_side_in(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_AXIS_LEFT_SIDE, FRONT_AXIS_LEFT_SIDE_ZERO + AXIS_OFFSET_IN, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_AXIS_LEFT_SIDE, 0))
    return AXIS_MOVE_DURATION_SEC


## FRONT_AXIS_LEFT_CENTER
async def front_axis_left_center_out(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_AXIS_LEFT_CENTER, FRONT_AXIS_LEFT_CENTER_ZERO + AXIS_OFFSET_OUT, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_AXIS_LEFT_CENTER, 1))
    return AXIS_MOVE_DURATION_SEC


async def front_axis_left_center_in(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_AXIS_LEFT_CENTER, FRONT_AXIS_LEFT_CENTER_ZERO + AXIS_OFFSET_IN, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_AXIS_LEFT_CENTER, 0))
    return AXIS_MOVE_DURATION_SEC


## FRONT_AXIS_RIGHT_CENTER
async def front_axis_right_center_out(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_AXIS_RIGHT_CENTER, FRONT_AXIS_RIGHT_CENTER_ZERO + AXIS_OFFSET_OUT, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_AXIS_RIGHT_CENTER, 1))
    return AXIS_MOVE_DURATION_SEC


async def front_axis_right_center_in(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_AXIS_RIGHT_CENTER, FRONT_AXIS_RIGHT_CENTER_ZERO + AXIS_OFFSET_IN, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_AXIS_RIGHT_CENTER, 0))
    return AXIS_MOVE_DURATION_SEC


## FRONT_AXIS_RIGHT_SIDE
async def front_axis_right_side_out(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_AXIS_RIGHT_SIDE, FRONT_AXIS_RIGHT_SIDE_ZERO + AXIS_OFFSET_OUT, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_AXIS_RIGHT_SIDE, 1))
    return AXIS_MOVE_DURATION_SEC


async def front_axis_right_side_in(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_AXIS_RIGHT_SIDE, FRONT_AXIS_RIGHT_SIDE_ZERO + AXIS_OFFSET_IN, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_AXIS_RIGHT_SIDE, 0))
    return AXIS_MOVE_DURATION_SEC


## FRONT_ARM_LEFT
async def front_arm_left_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_ARM_LEFT, FRONT_ARM_LEFT_ZERO + ARM_OFFSET_OPEN, reg_only=reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_ARM_LEFT, 1))
    return ARM_MOVE_DURATION_SEC


async def front_arm_left_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_ARM_LEFT, FRONT_ARM_LEFT_ZERO + ARM_OFFSET_CLOSE, reg_only=reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_ARM_LEFT, 0))
    return ARM_MOVE_DURATION_SEC


## FRONT_ARM_RIGHT
async def front_arm_right_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_ARM_RIGHT, FRONT_ARM_RIGHT_ZERO + ARM_OFFSET_OPEN, reg_only=reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_ARM_RIGHT, 1))
    return ARM_MOVE_DURATION_SEC


async def front_arm_right_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_ARM_RIGHT, FRONT_ARM_RIGHT_ZERO + ARM_OFFSET_CLOSE, reg_only=reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_ARM_RIGHT, 0))
    return ARM_MOVE_DURATION_SEC


## FRONT_SCISSOR_LEFT
async def front_scissor_left_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_SCISSOR_LEFT, FRONT_SCISSOR_LEFT_ZERO + SCISSOR_OFFSET_OPEN, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_SCISSOR_LEFT, 1))
    return SCISSOR_MOVE_DURATION_SEC


async def front_scissor_left_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_SCISSOR_LEFT, FRONT_SCISSOR_LEFT_ZERO + SCISSOR_OFFSET_CLOSE, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_SCISSOR_LEFT, 0))
    return SCISSOR_MOVE_DURATION_SEC


## FRONT_SCISSOR_RIGHT
async def front_scissor_right_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_SCISSOR_RIGHT, FRONT_SCISSOR_RIGHT_ZERO + SCISSOR_OFFSET_OPEN, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_SCISSOR_RIGHT, 1))
    return SCISSOR_MOVE_DURATION_SEC


async def front_scissor_right_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_SCISSOR_RIGHT, FRONT_SCISSOR_RIGHT_ZERO + SCISSOR_OFFSET_CLOSE, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_SCISSOR_RIGHT, 0))
    return SCISSOR_MOVE_DURATION_SEC


# SC Servos - Back


## BACK_GRIP_LEFT_SIDE
async def back_grip_left_side_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_GRIP_LEFT_SIDE, BACK_GRIP_LEFT_SIDE_ZERO + GRIP_OFFSET_OPEN, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_GRIP_LEFT_SIDE, 1))
    return GRIP_MOVE_DURATION_SEC


async def back_grip_left_side_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_GRIP_LEFT_SIDE, BACK_GRIP_LEFT_SIDE_ZERO + GRIP_OFFSET_CLOSE, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_GRIP_LEFT_SIDE, 0))
    return GRIP_MOVE_DURATION_SEC


## BACK_GRIP_LEFT_CENTER
async def back_grip_left_center_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_GRIP_LEFT_CENTER, BACK_GRIP_LEFT_CENTER_ZERO + GRIP_OFFSET_OPEN, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_GRIP_LEFT_CENTER, 1))
    return GRIP_MOVE_DURATION_SEC


async def back_grip_left_center_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_GRIP_LEFT_CENTER, BACK_GRIP_LEFT_CENTER_ZERO + GRIP_OFFSET_CLOSE, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_GRIP_LEFT_CENTER, 0))
    return GRIP_MOVE_DURATION_SEC


## BACK_GRIP_RIGHT_CENTER
async def back_grip_right_center_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_GRIP_RIGHT_CENTER, BACK_GRIP_RIGHT_CENTER_ZERO + GRIP_OFFSET_OPEN, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_GRIP_RIGHT_CENTER, 1))
    return GRIP_MOVE_DURATION_SEC


async def back_grip_right_center_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_GRIP_RIGHT_CENTER, BACK_GRIP_RIGHT_CENTER_ZERO + GRIP_OFFSET_CLOSE, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_GRIP_RIGHT_CENTER, 0))
    return GRIP_MOVE_DURATION_SEC


## BACK_GRIP_RIGHT_SIDE
async def back_grip_right_side_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_GRIP_RIGHT_SIDE, BACK_GRIP_RIGHT_SIDE_ZERO + GRIP_OFFSET_OPEN, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_GRIP_RIGHT_SIDE, 1))
    return GRIP_MOVE_DURATION_SEC


async def back_grip_right_side_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_GRIP_RIGHT_SIDE, BACK_GRIP_RIGHT_SIDE_ZERO + GRIP_OFFSET_CLOSE, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_GRIP_RIGHT_SIDE, 0))
    return GRIP_MOVE_DURATION_SEC


## BACK_AXIS_LEFT_SIDE
async def back_axis_left_side_out(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_AXIS_LEFT_SIDE, BACK_AXIS_LEFT_SIDE_ZERO + AXIS_OFFSET_OUT, reg_only=reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_AXIS_LEFT_SIDE, 1))
    return AXIS_MOVE_DURATION_SEC


async def back_axis_left_side_in(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_AXIS_LEFT_SIDE, BACK_AXIS_LEFT_SIDE_ZERO + AXIS_OFFSET_IN, reg_only=reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_AXIS_LEFT_SIDE, 0))
    return AXIS_MOVE_DURATION_SEC


## BACK_AXIS_LEFT_CENTER
async def back_axis_left_center_out(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_AXIS_LEFT_CENTER, BACK_AXIS_LEFT_CENTER_ZERO + AXIS_OFFSET_OUT, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_AXIS_LEFT_CENTER, 1))
    return AXIS_MOVE_DURATION_SEC


async def back_axis_left_center_in(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_AXIS_LEFT_CENTER, BACK_AXIS_LEFT_CENTER_ZERO + AXIS_OFFSET_IN, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_AXIS_LEFT_CENTER, 0))
    return AXIS_MOVE_DURATION_SEC


## BACK_AXIS_RIGHT_CENTER
async def back_axis_right_center_out(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_AXIS_RIGHT_CENTER, BACK_AXIS_RIGHT_CENTER_ZERO + AXIS_OFFSET_OUT, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_AXIS_RIGHT_CENTER, 1))
    return AXIS_MOVE_DURATION_SEC


async def back_axis_right_center_in(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_AXIS_RIGHT_CENTER, BACK_AXIS_RIGHT_CENTER_ZERO + AXIS_OFFSET_IN, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_AXIS_RIGHT_CENTER, 0))
    return AXIS_MOVE_DURATION_SEC


# BACK_AXIS_RIGHT_SIDE
async def back_axis_right_side_out(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_AXIS_RIGHT_SIDE, BACK_AXIS_RIGHT_SIDE_ZERO + AXIS_OFFSET_OUT, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_AXIS_RIGHT_SIDE, 1))
    return AXIS_MOVE_DURATION_SEC


async def back_axis_right_side_in(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_AXIS_RIGHT_SIDE, BACK_AXIS_RIGHT_SIDE_ZERO + AXIS_OFFSET_IN, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_AXIS_RIGHT_SIDE, 0))
    return AXIS_MOVE_DURATION_SEC


## BACK_ARM_LEFT
async def back_arm_left_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_ARM_LEFT, BACK_ARM_LEFT_ZERO + ARM_OFFSET_OPEN, reg_only=reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_ARM_LEFT, 1))
    return ARM_MOVE_DURATION_SEC


async def back_arm_left_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_ARM_LEFT, BACK_ARM_LEFT_ZERO + ARM_OFFSET_CLOSE, reg_only=reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_ARM_LEFT, 0))
    return ARM_MOVE_DURATION_SEC


## BACK_ARM_RIGHT
async def back_arm_right_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_ARM_RIGHT, BACK_ARM_RIGHT_ZERO + ARM_OFFSET_OPEN, reg_only=reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_ARM_RIGHT, 1))
    return ARM_MOVE_DURATION_SEC


async def back_arm_right_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_ARM_RIGHT, BACK_ARM_RIGHT_ZERO + ARM_OFFSET_CLOSE, reg_only=reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_ARM_RIGHT, 0))
    return ARM_MOVE_DURATION_SEC


## BACK_SCISSOR_LEFT
async def back_scissor_left_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_SCISSOR_LEFT, BACK_SCISSOR_LEFT_ZERO + SCISSOR_OFFSET_OPEN, reg_only=reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_SCISSOR_LEFT, 1))
    return SCISSOR_MOVE_DURATION_SEC


async def back_scissor_left_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_SCISSOR_LEFT, BACK_SCISSOR_LEFT_ZERO + SCISSOR_OFFSET_CLOSE, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_SCISSOR_LEFT, 0))
    return SCISSOR_MOVE_DURATION_SEC


## BACK_SCISSOR_RIGHT
async def back_scissor_right_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_SCISSOR_RIGHT, BACK_SCISSOR_RIGHT_ZERO + SCISSOR_OFFSET_OPEN, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_SCISSOR_RIGHT, 1))
    return SCISSOR_MOVE_DURATION_SEC


async def back_scissor_right_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_SCISSOR_RIGHT, BACK_SCISSOR_RIGHT_ZERO + SCISSOR_OFFSET_CLOSE, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_SCISSOR_RIGHT, 0))
    return SCISSOR_MOVE_DURATION_SEC


# Multi-commands
async def front_arms_open(planner: "Planner") -> float:
    await front_arm_left_open(planner, reg_only=True)
    await front_arm_right_open(planner, reg_only=True)
    planner.scservos.action()
    return ARM_MOVE_DURATION_SEC


async def front_arms_close(planner: "Planner") -> float:
    await front_arm_left_close(planner, reg_only=True)
    await front_arm_right_close(planner, reg_only=True)
    planner.scservos.action()
    return ARM_MOVE_DURATION_SEC


async def front_grips_open(planner: "Planner") -> float:
    await front_grip_left_side_open(planner, reg_only=True)
    await front_grip_left_center_open(planner, reg_only=True)
    await front_grip_right_center_open(planner, reg_only=True)
    await front_grip_right_side_open(planner, reg_only=True)
    planner.scservos.action()
    return GRIP_MOVE_DURATION_SEC


async def front_grips_close(planner: "Planner") -> float:
    await front_grip_left_side_close(planner, reg_only=True)
    await front_grip_left_center_close(planner, reg_only=True)
    await front_grip_right_center_close(planner, reg_only=True)
    await front_grip_right_side_close(planner, reg_only=True)
    planner.scservos.action()
    return GRIP_MOVE_DURATION_SEC


async def front_scissors_open(planner: "Planner") -> float:
    await front_scissor_left_open(planner, reg_only=True)
    await front_scissor_right_open(planner, reg_only=True)
    planner.scservos.action()
    return SCISSOR_MOVE_DURATION_SEC


async def front_scissors_close(planner: "Planner") -> float:
    await front_scissor_left_close(planner, reg_only=True)
    await front_scissor_right_close(planner, reg_only=True)
    planner.scservos.action()
    return SCISSOR_MOVE_DURATION_SEC


async def back_arms_open(planner: "Planner") -> float:
    await back_arm_left_open(planner, reg_only=True)
    await back_arm_right_open(planner, reg_only=True)
    planner.scservos.action()
    return ARM_MOVE_DURATION_SEC


async def back_arms_close(planner: "Planner") -> float:
    await back_arm_left_close(planner, reg_only=True)
    await back_arm_right_close(planner, reg_only=True)
    planner.scservos.action()
    return ARM_MOVE_DURATION_SEC


async def back_grips_open(planner: "Planner") -> float:
    await back_grip_left_side_open(planner, reg_only=True)
    await back_grip_left_center_open(planner, reg_only=True)
    await back_grip_right_center_open(planner, reg_only=True)
    await back_grip_right_side_open(planner, reg_only=True)
    planner.scservos.action()
    return GRIP_MOVE_DURATION_SEC


async def back_grips_close(planner: "Planner") -> float:
    await back_grip_left_side_close(planner, reg_only=True)
    await back_grip_left_center_close(planner, reg_only=True)
    await back_grip_right_center_close(planner, reg_only=True)
    await back_grip_right_side_close(planner, reg_only=True)
    planner.scservos.action()
    return GRIP_MOVE_DURATION_SEC


async def back_scissors_open(planner: "Planner") -> float:
    await back_scissor_left_open(planner, reg_only=True)
    await back_scissor_right_open(planner, reg_only=True)
    planner.scservos.action()
    return SCISSOR_MOVE_DURATION_SEC


async def back_scissors_close(planner: "Planner") -> float:
    await back_scissor_left_close(planner, reg_only=True)
    await back_scissor_right_close(planner, reg_only=True)
    planner.scservos.action()
    return SCISSOR_MOVE_DURATION_SEC
