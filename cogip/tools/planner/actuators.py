import asyncio
from typing import TYPE_CHECKING

from cogip.models.actuators import (
    PositionalActuatorCommand,
    PositionalActuatorEnum,
)
from . import logger
from .scservos import SCServoEnum

if TYPE_CHECKING:
    from cogip.tools.planner.planner import Planner

# Lift positions
LIFT_DOWN = 0
LIFT_MID = 80
LIFT_UP = 130

# Duration of actuator movements is seconds
GRIP_MOVE_DURATION_SEC = 0.3
AXIS_MOVE_DURATION_SEC = 0.5
ARM_MOVE_DURATION_SEC = 0.5
LIFT_MOVE_DURATION_SEC = 1.5
SCISSOR_MOVE_DURATION_SEC = 0.5
NINJA_ARM_MOVE_DURATION_SEC = 0.5

# Define center and offset for servos positions
FRONT_GRIP_LEFT_SIDE_ZERO = 528
FRONT_GRIP_LEFT_CENTER_ZERO = 672
FRONT_GRIP_RIGHT_CENTER_ZERO = 646
FRONT_GRIP_RIGHT_SIDE_ZERO = 522
FRONT_AXIS_LEFT_SIDE_ZERO = 855
FRONT_AXIS_LEFT_CENTER_ZERO = 866
FRONT_AXIS_RIGHT_CENTER_ZERO = 880
FRONT_AXIS_RIGHT_SIDE_ZERO = 726
FRONT_ARM_LEFT_ZERO = 373
FRONT_ARM_RIGHT_ZERO = 321
FRONT_SCISSOR_LEFT_OPEN = 753  # ZERO
FRONT_SCISSOR_LEFT_CLOSE = 626
FRONT_SCISSOR_RIGHT_OPEN = 743  # ZERO
FRONT_SCISSOR_RIGHT_CLOSE = 841

BACK_GRIP_LEFT_SIDE_ZERO = 753
BACK_GRIP_LEFT_CENTER_ZERO = 684
BACK_GRIP_RIGHT_CENTER_ZERO = 605
BACK_GRIP_RIGHT_SIDE_ZERO = 566
BACK_AXIS_LEFT_SIDE_ZERO = 856
BACK_AXIS_LEFT_CENTER_ZERO = 889
BACK_AXIS_RIGHT_CENTER_ZERO = 835
BACK_AXIS_RIGHT_SIDE_ZERO = 892
BACK_ARM_LEFT_ZERO = 350
BACK_ARM_RIGHT_ZERO = 316
BACK_SCISSOR_LEFT_OPEN = 190  # ZERO
BACK_SCISSOR_LEFT_CLOSE = 295
BACK_SCISSOR_RIGHT_OPEN = 550  # ZERO
BACK_SCISSOR_RIGHT_CLOSE = 410

NINJA_ARM_LEFT_ZERO = 500  # Front  # TO CALIBRATE
NINJA_ARM_RIGHT_ZERO = 500  # Front  # TO CALIBRATE

GRIP_OFFSET_OPEN = 70
GRIP_OFFSET_CLOSE = -40
AXIS_OFFSET_OUT = 0
AXIS_OFFSET_IN = -580
ARM_OFFSET_OPEN = 393
ARM_OFFSET_CLOSE = -45
SCISSOR_OFFSET_OPEN = 135
SCISSOR_OFFSET_CLOSE = 0
NINJA_ARM_OFFSET_CLOSE = -300  # TO CALIBRATE
NINJA_ARM_OFFSET_FRONT = 0
NINJA_ARM_OFFSET_SIDE = 300  # TO CALIBRATE


async def actuators_init(planner: "Planner"):
    """
    Send actuators initialization command to the firmware.
    """
    if planner.robot_id == 1:
        await front_lift_init(planner)
        await back_lift_init(planner)
        await front_arms_close(planner)
        await back_arms_close(planner)
        await front_grips_close(planner)
        await back_grips_close(planner)
        await front_scissors_open(planner)
        duration = await back_scissors_open(planner)
        await asyncio.sleep(duration)
        await front_axis_left_side_out(planner)
        await front_axis_left_center_out(planner)
        await front_axis_right_center_out(planner)
        duration = await front_axis_right_side_out(planner)
        await asyncio.sleep(duration)
        await front_scissors_close(planner)
        await back_scissors_close(planner)
    elif planner.robot_id == 2:
        await ninja_arms_close(planner)


# Positional Motors
async def positional_motor_command(
    planner: "Planner",
    motor: PositionalActuatorEnum,
    command: int,
    speed: int = 100,
    timeout: int = 2000,
) -> float:
    logger.info(f"actuators: Sending positional motor command: {motor.name}={command} speed={speed} timeout={timeout}")
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


async def front_lift_init(planner: "Planner"):
    logger.info("actuators: Initializing front lift")
    await planner.sio_ns.emit("actuator_init", PositionalActuatorEnum.FRONT_LIFT)
    await planner.sio_ns.emit("lift", (PositionalActuatorEnum.FRONT_LIFT, LIFT_DOWN))


async def front_lift_down(planner: "Planner", pose: int = LIFT_DOWN, speed: int = 100, timeout: int = 5000) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.FRONT_LIFT, pose, speed, timeout)
    await planner.sio_ns.emit("lift", (PositionalActuatorEnum.FRONT_LIFT, pose))
    return LIFT_MOVE_DURATION_SEC


async def front_lift_mid(planner: "Planner", pose: int = LIFT_MID, speed: int = 100, timeout: int = 5000) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.FRONT_LIFT, pose, speed, timeout)
    await planner.sio_ns.emit("lift", (PositionalActuatorEnum.FRONT_LIFT, pose))
    return LIFT_MOVE_DURATION_SEC / 2


async def front_lift_up(planner: "Planner", pose: int = LIFT_UP, speed: int = 100, timeout: int = 5000) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.FRONT_LIFT, pose, speed, timeout)
    await planner.sio_ns.emit("lift", (PositionalActuatorEnum.FRONT_LIFT, pose))
    return LIFT_MOVE_DURATION_SEC


async def back_lift_init(planner: "Planner"):
    logger.info("actuators: Initializing back lift")
    await planner.sio_ns.emit("actuator_init", PositionalActuatorEnum.BACK_LIFT)
    await planner.sio_ns.emit("lift", (PositionalActuatorEnum.BACK_LIFT, LIFT_DOWN))


async def back_lift_down(planner: "Planner", pose: int = LIFT_DOWN, speed: int = 100, timeout: int = 5000) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.BACK_LIFT, pose, speed, timeout)
    await planner.sio_ns.emit("lift", (PositionalActuatorEnum.BACK_LIFT, pose))
    return LIFT_MOVE_DURATION_SEC


async def back_lift_mid(planner: "Planner", pose: int = LIFT_MID, speed: int = 100, timeout: int = 5000) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.BACK_LIFT, pose, speed, timeout)
    await planner.sio_ns.emit("lift", (PositionalActuatorEnum.BACK_LIFT, pose))
    return LIFT_MOVE_DURATION_SEC / 2


async def back_lift_up(planner: "Planner", pose: int = LIFT_UP, speed: int = 100, timeout: int = 5000) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.BACK_LIFT, pose, speed, timeout)
    await planner.sio_ns.emit("lift", (PositionalActuatorEnum.BACK_LIFT, pose))
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
async def front_axis_left_side_out(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_AXIS_LEFT_SIDE, FRONT_AXIS_LEFT_SIDE_ZERO + AXIS_OFFSET_OUT, speed, reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_AXIS_LEFT_SIDE, 1))
    return AXIS_MOVE_DURATION_SEC


async def front_axis_left_side_in(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_AXIS_LEFT_SIDE, FRONT_AXIS_LEFT_SIDE_ZERO + AXIS_OFFSET_IN, speed, reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_AXIS_LEFT_SIDE, 0))
    return AXIS_MOVE_DURATION_SEC


## FRONT_AXIS_LEFT_CENTER
async def front_axis_left_center_out(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_AXIS_LEFT_CENTER, FRONT_AXIS_LEFT_CENTER_ZERO + AXIS_OFFSET_OUT, speed, reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_AXIS_LEFT_CENTER, 1))
    return AXIS_MOVE_DURATION_SEC


async def front_axis_left_center_in(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_AXIS_LEFT_CENTER, FRONT_AXIS_LEFT_CENTER_ZERO + AXIS_OFFSET_IN, speed, reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_AXIS_LEFT_CENTER, 0))
    return AXIS_MOVE_DURATION_SEC


## FRONT_AXIS_RIGHT_CENTER
async def front_axis_right_center_out(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_AXIS_RIGHT_CENTER, FRONT_AXIS_RIGHT_CENTER_ZERO + AXIS_OFFSET_OUT, speed, reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_AXIS_RIGHT_CENTER, 1))
    return AXIS_MOVE_DURATION_SEC


async def front_axis_right_center_in(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_AXIS_RIGHT_CENTER, FRONT_AXIS_RIGHT_CENTER_ZERO + AXIS_OFFSET_IN, speed, reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_AXIS_RIGHT_CENTER, 0))
    return AXIS_MOVE_DURATION_SEC


## FRONT_AXIS_RIGHT_SIDE
async def front_axis_right_side_out(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_AXIS_RIGHT_SIDE, FRONT_AXIS_RIGHT_SIDE_ZERO + AXIS_OFFSET_OUT, speed, reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_AXIS_RIGHT_SIDE, 1))
    return AXIS_MOVE_DURATION_SEC


async def front_axis_right_side_in(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.FRONT_AXIS_RIGHT_SIDE, FRONT_AXIS_RIGHT_SIDE_ZERO + AXIS_OFFSET_IN, speed, reg_only
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
async def front_scissor_left_open(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_SCISSOR_LEFT, FRONT_SCISSOR_LEFT_OPEN, speed=speed, reg_only=reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_SCISSOR_LEFT, 1))
    return SCISSOR_MOVE_DURATION_SEC


async def front_scissor_left_close(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_SCISSOR_LEFT, FRONT_SCISSOR_LEFT_CLOSE, speed=speed, reg_only=reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_SCISSOR_LEFT, 0))
    return SCISSOR_MOVE_DURATION_SEC


## FRONT_SCISSOR_RIGHT
async def front_scissor_right_open(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_SCISSOR_RIGHT, FRONT_SCISSOR_RIGHT_OPEN, speed=speed, reg_only=reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.FRONT_SCISSOR_RIGHT, 1))
    return SCISSOR_MOVE_DURATION_SEC


async def front_scissor_right_close(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_SCISSOR_RIGHT, FRONT_SCISSOR_RIGHT_CLOSE, speed=speed, reg_only=reg_only)
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
async def back_grip_right_side_open(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_GRIP_RIGHT_SIDE, BACK_GRIP_RIGHT_SIDE_ZERO + GRIP_OFFSET_OPEN, speed, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_GRIP_RIGHT_SIDE, 1))
    return GRIP_MOVE_DURATION_SEC


async def back_grip_right_side_close(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_GRIP_RIGHT_SIDE, BACK_GRIP_RIGHT_SIDE_ZERO + GRIP_OFFSET_CLOSE, speed, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_GRIP_RIGHT_SIDE, 0))
    return GRIP_MOVE_DURATION_SEC


## BACK_AXIS_LEFT_SIDE
async def back_axis_left_side_out(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_AXIS_LEFT_SIDE, BACK_AXIS_LEFT_SIDE_ZERO + AXIS_OFFSET_OUT, speed, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_AXIS_LEFT_SIDE, 1))
    return AXIS_MOVE_DURATION_SEC


async def back_axis_left_side_in(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_AXIS_LEFT_SIDE, BACK_AXIS_LEFT_SIDE_ZERO + AXIS_OFFSET_IN, speed, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_AXIS_LEFT_SIDE, 0))
    return AXIS_MOVE_DURATION_SEC


## BACK_AXIS_LEFT_CENTER
async def back_axis_left_center_out(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_AXIS_LEFT_CENTER, BACK_AXIS_LEFT_CENTER_ZERO + AXIS_OFFSET_OUT, speed, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_AXIS_LEFT_CENTER, 1))
    return AXIS_MOVE_DURATION_SEC


async def back_axis_left_center_in(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_AXIS_LEFT_CENTER, BACK_AXIS_LEFT_CENTER_ZERO + AXIS_OFFSET_IN, speed, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_AXIS_LEFT_CENTER, 0))
    return AXIS_MOVE_DURATION_SEC


## BACK_AXIS_RIGHT_CENTER
async def back_axis_right_center_out(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_AXIS_RIGHT_CENTER, BACK_AXIS_RIGHT_CENTER_ZERO + AXIS_OFFSET_OUT, speed, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_AXIS_RIGHT_CENTER, 1))
    return AXIS_MOVE_DURATION_SEC


async def back_axis_right_center_in(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_AXIS_RIGHT_CENTER, BACK_AXIS_RIGHT_CENTER_ZERO + AXIS_OFFSET_IN, speed, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_AXIS_RIGHT_CENTER, 0))
    return AXIS_MOVE_DURATION_SEC


# BACK_AXIS_RIGHT_SIDE
async def back_axis_right_side_out(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_AXIS_RIGHT_SIDE, BACK_AXIS_RIGHT_SIDE_ZERO + AXIS_OFFSET_OUT, speed, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_AXIS_RIGHT_SIDE, 1))
    return AXIS_MOVE_DURATION_SEC


async def back_axis_right_side_in(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.BACK_AXIS_RIGHT_SIDE, BACK_AXIS_RIGHT_SIDE_ZERO + AXIS_OFFSET_IN, speed, reg_only=reg_only
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
async def back_scissor_left_open(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_SCISSOR_LEFT, BACK_SCISSOR_LEFT_OPEN, speed=speed, reg_only=reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_SCISSOR_LEFT, 1))
    return SCISSOR_MOVE_DURATION_SEC


async def back_scissor_left_close(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_SCISSOR_LEFT, BACK_SCISSOR_LEFT_CLOSE, speed=speed, reg_only=reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_SCISSOR_LEFT, 0))
    return SCISSOR_MOVE_DURATION_SEC


## BACK_SCISSOR_RIGHT
async def back_scissor_right_open(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_SCISSOR_RIGHT, BACK_SCISSOR_RIGHT_OPEN, speed=speed, reg_only=reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_SCISSOR_RIGHT, 1))
    return SCISSOR_MOVE_DURATION_SEC


async def back_scissor_right_close(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_SCISSOR_RIGHT, BACK_SCISSOR_RIGHT_CLOSE, speed=speed, reg_only=reg_only)
    await planner.sio_ns.emit("servo", (SCServoEnum.BACK_SCISSOR_RIGHT, 0))
    return SCISSOR_MOVE_DURATION_SEC


## Ninja Arms
async def ninja_arm_left_close(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.NINJA_ARM_LEFT, NINJA_ARM_LEFT_ZERO + NINJA_ARM_OFFSET_CLOSE, speed=speed, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.NINJA_ARM_LEFT, 0))
    return NINJA_ARM_MOVE_DURATION_SEC


async def ninja_arm_left_front(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.NINJA_ARM_LEFT, NINJA_ARM_LEFT_ZERO + NINJA_ARM_OFFSET_FRONT, speed=speed, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.NINJA_ARM_LEFT, 1))
    return NINJA_ARM_MOVE_DURATION_SEC


async def ninja_arm_left_side(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.NINJA_ARM_LEFT, NINJA_ARM_LEFT_ZERO + NINJA_ARM_OFFSET_SIDE, speed=speed, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.NINJA_ARM_LEFT, 2))
    return NINJA_ARM_MOVE_DURATION_SEC


async def ninja_arm_right_close(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.NINJA_ARM_RIGHT, NINJA_ARM_RIGHT_ZERO - NINJA_ARM_OFFSET_CLOSE, speed=speed, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.NINJA_ARM_RIGHT, 0))
    return NINJA_ARM_MOVE_DURATION_SEC


async def ninja_arm_right_front(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.NINJA_ARM_RIGHT, NINJA_ARM_RIGHT_ZERO - NINJA_ARM_OFFSET_FRONT, speed=speed, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.NINJA_ARM_RIGHT, 1))
    return NINJA_ARM_MOVE_DURATION_SEC


async def ninja_arm_right_side(planner: "Planner", speed: int = 1000, reg_only: bool = False) -> float:
    planner.scservos.set(
        SCServoEnum.NINJA_ARM_RIGHT, NINJA_ARM_RIGHT_ZERO - NINJA_ARM_OFFSET_SIDE, speed=speed, reg_only=reg_only
    )
    await planner.sio_ns.emit("servo", (SCServoEnum.NINJA_ARM_RIGHT, 2))
    return NINJA_ARM_MOVE_DURATION_SEC


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


async def front_scissors_open(planner: "Planner", speed: int = 1000) -> float:
    await front_scissor_left_open(planner, speed=speed, reg_only=True)
    await front_scissor_right_open(planner, speed=speed, reg_only=True)
    planner.scservos.action()
    return SCISSOR_MOVE_DURATION_SEC


async def front_scissors_close(planner: "Planner", speed: int = 1000) -> float:
    await front_scissor_left_close(planner, speed=speed, reg_only=True)
    await front_scissor_right_close(planner, speed=speed, reg_only=True)
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


async def back_scissors_open(planner: "Planner", speed: int = 1000) -> float:
    await back_scissor_left_open(planner, speed=speed, reg_only=True)
    await back_scissor_right_open(planner, speed=speed, reg_only=True)
    planner.scservos.action()
    return SCISSOR_MOVE_DURATION_SEC


async def back_scissors_close(planner: "Planner", speed: int = 1000) -> float:
    await back_scissor_left_close(planner, speed=speed, reg_only=True)
    await back_scissor_right_close(planner, speed=speed, reg_only=True)
    planner.scservos.action()
    return SCISSOR_MOVE_DURATION_SEC


async def ninja_arms_close(planner: "Planner", speed: int = 1000) -> float:
    await ninja_arm_left_close(planner, speed=speed, reg_only=True)
    await ninja_arm_right_close(planner, speed=speed, reg_only=True)
    planner.scservos.action()
    return NINJA_ARM_MOVE_DURATION_SEC


async def ninja_arms_front(planner: "Planner", speed: int = 1000) -> float:
    await ninja_arm_left_front(planner, speed=speed, reg_only=True)
    await ninja_arm_right_front(planner, speed=speed, reg_only=True)
    planner.scservos.action()
    return NINJA_ARM_MOVE_DURATION_SEC


async def ninja_arms_side(planner: "Planner", speed: int = 1000) -> float:
    await ninja_arm_left_side(planner, speed=speed, reg_only=True)
    await ninja_arm_right_side(planner, speed=speed, reg_only=True)
    planner.scservos.action()
    return NINJA_ARM_MOVE_DURATION_SEC
