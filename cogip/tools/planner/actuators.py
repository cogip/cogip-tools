from typing import TYPE_CHECKING

from cogip.models.actuators import (
    PositionalActuatorCommand,
    PositionalActuatorEnum,
)
from .scservos import SCServoEnum

if TYPE_CHECKING:
    from cogip.tools.planner.planner import Planner

# Duration of actuator movements is seconds
GRIP_MOVE_DURATION_SEC = 0.5
AXIS_MOVE_DURATION_SEC = 0.5
ARM_MOVE_DURATION_SEC = 0.5
LIFT_MOVE_DURATION_SEC = 1.0


async def actuators_init(planner: "Planner"):
    """
    Send actuators initialization command to the firmware.
    """
    await planner.sio_ns.emit("actuator_init")


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
    await positional_motor_command(planner, PositionalActuatorEnum.FRONT_MOTOR_LIFT, 0, speed)
    return LIFT_MOVE_DURATION_SEC


async def front_lift_mid(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.FRONT_MOTOR_LIFT, 50, speed)
    return LIFT_MOVE_DURATION_SEC


async def front_lift_up(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.FRONT_MOTOR_LIFT, 100, speed)
    return LIFT_MOVE_DURATION_SEC


async def back_lift_down(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.BACK_MOTOR_LIFT, 0, speed)
    return LIFT_MOVE_DURATION_SEC


async def back_lift_mid(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.BACK_MOTOR_LIFT, 50, speed)
    return LIFT_MOVE_DURATION_SEC / 2


async def back_lift_up(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.BACK_MOTOR_LIFT, 100, speed)
    return LIFT_MOVE_DURATION_SEC / 2


# SC Servos - Front


## FRONT_GRIP_LEFT_SIDE
async def front_grip_left_side_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_GRIP_LEFT_SIDE, 0, reg_only=reg_only)
    return GRIP_MOVE_DURATION_SEC


async def front_grip_left_side_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_GRIP_LEFT_SIDE, 0, reg_only=reg_only)
    return GRIP_MOVE_DURATION_SEC


## FRONT_GRIP_LEFT_CENTER
async def front_grip_left_center_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_GRIP_LEFT_CENTER, 0, reg_only=reg_only)
    return GRIP_MOVE_DURATION_SEC


async def front_grip_left_center_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_GRIP_LEFT_CENTER, 0, reg_only=reg_only)
    return GRIP_MOVE_DURATION_SEC


## FRONT_GRIP_RIGHT_CENTER
async def front_grip_right_center_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_GRIP_RIGHT_CENTER, 0, reg_only=reg_only)
    return GRIP_MOVE_DURATION_SEC


async def front_grip_right_center_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_GRIP_RIGHT_CENTER, 0, reg_only=reg_only)
    return GRIP_MOVE_DURATION_SEC


## FRONT_GRIP_RIGHT_SIDE
async def front_grip_right_side_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_GRIP_RIGHT_SIDE, 0, reg_only=reg_only)
    return GRIP_MOVE_DURATION_SEC


async def front_grip_right_side_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_GRIP_RIGHT_SIDE, 0, reg_only=reg_only)
    return GRIP_MOVE_DURATION_SEC


## FRONT_AXIS_LEFT_SIDE
async def front_axis_left_side_out(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_AXIS_LEFT_SIDE, 0, reg_only=reg_only)
    return AXIS_MOVE_DURATION_SEC


async def front_axis_left_side_in(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_AXIS_LEFT_SIDE, 0, reg_only=reg_only)
    return AXIS_MOVE_DURATION_SEC


## FRONT_AXIS_LEFT_CENTER
async def front_axis_left_center_out(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_AXIS_LEFT_CENTER, 0, reg_only=reg_only)
    return AXIS_MOVE_DURATION_SEC


async def front_axis_left_center_in(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_AXIS_LEFT_CENTER, 0, reg_only=reg_only)
    return AXIS_MOVE_DURATION_SEC


## FRONT_AXIS_RIGHT_CENTER
async def front_axis_right_center_out(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_AXIS_RIGHT_CENTER, 0, reg_only=reg_only)
    return AXIS_MOVE_DURATION_SEC


async def front_axis_right_center_in(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_AXIS_RIGHT_CENTER, 0, reg_only=reg_only)
    return AXIS_MOVE_DURATION_SEC


## FRONT_AXIS_RIGHT_SIDE
async def front_axis_right_side_out(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_AXIS_RIGHT_SIDE, 0, reg_only=reg_only)
    return AXIS_MOVE_DURATION_SEC


async def front_axis_right_side_in(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_AXIS_RIGHT_SIDE, 0, reg_only=reg_only)
    return AXIS_MOVE_DURATION_SEC


## FRONT_ARM_LEFT
async def front_arm_left_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_ARM_LEFT, 636, reg_only=reg_only)
    return ARM_MOVE_DURATION_SEC


async def front_arm_left_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_ARM_LEFT, 305, reg_only=reg_only)
    return ARM_MOVE_DURATION_SEC


## FRONT_ARM_RIGHT
async def front_arm_right_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_ARM_RIGHT, 528, reg_only=reg_only)
    return ARM_MOVE_DURATION_SEC


async def front_arm_right_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.FRONT_ARM_RIGHT, 297, reg_only=reg_only)
    return ARM_MOVE_DURATION_SEC


# SC Servos - Back


## BACK_GRIP_LEFT_SIDE
async def back_grip_left_side_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_GRIP_LEFT_SIDE, 0, reg_only=reg_only)
    return GRIP_MOVE_DURATION_SEC


async def back_grip_left_side_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_GRIP_LEFT_SIDE, 0, reg_only=reg_only)
    return GRIP_MOVE_DURATION_SEC


## BACK_GRIP_LEFT_CENTER
async def back_grip_left_center_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_GRIP_LEFT_CENTER, 0, reg_only=reg_only)
    return GRIP_MOVE_DURATION_SEC


async def back_grip_left_center_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_GRIP_LEFT_CENTER, 0, reg_only=reg_only)
    return GRIP_MOVE_DURATION_SEC


## BACK_GRIP_RIGHT_CENTER
async def back_grip_right_center_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_GRIP_RIGHT_CENTER, 0, reg_only=reg_only)
    return GRIP_MOVE_DURATION_SEC


async def back_grip_right_center_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_GRIP_RIGHT_CENTER, 0, reg_only=reg_only)
    return GRIP_MOVE_DURATION_SEC


## BACK_GRIP_RIGHT_SIDE
async def back_grip_right_side_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_GRIP_RIGHT_SIDE, 0, reg_only=reg_only)
    return GRIP_MOVE_DURATION_SEC


async def back_grip_right_side_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_GRIP_RIGHT_SIDE, 0, reg_only=reg_only)
    return GRIP_MOVE_DURATION_SEC


## BACK_AXIS_LEFT_SIDE
async def back_axis_left_side_out(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_AXIS_LEFT_SIDE, 0, reg_only=reg_only)
    return AXIS_MOVE_DURATION_SEC


async def back_axis_left_side_in(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_AXIS_LEFT_SIDE, 0, reg_only=reg_only)
    return AXIS_MOVE_DURATION_SEC


## BACK_AXIS_LEFT_CENTER
async def back_axis_left_center_out(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_AXIS_LEFT_CENTER, 0, reg_only=reg_only)
    return AXIS_MOVE_DURATION_SEC


async def back_axis_left_center_in(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_AXIS_LEFT_CENTER, 0, reg_only=reg_only)
    return AXIS_MOVE_DURATION_SEC


## BACK_AXIS_RIGHT_CENTER
async def back_axis_right_center_out(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_AXIS_RIGHT_CENTER, 0, reg_only=reg_only)
    return AXIS_MOVE_DURATION_SEC


async def back_axis_right_center_in(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_AXIS_RIGHT_CENTER, 0, reg_only=reg_only)
    return AXIS_MOVE_DURATION_SEC


# BACK_AXIS_RIGHT_SIDE
async def back_axis_right_side_out(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_AXIS_RIGHT_SIDE, 0, reg_only=reg_only)
    return AXIS_MOVE_DURATION_SEC


async def back_axis_right_side_in(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_AXIS_RIGHT_SIDE, 0, reg_only=reg_only)
    return AXIS_MOVE_DURATION_SEC


## BACK_ARM_LEFT
async def back_arm_left_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_ARM_LEFT, 0, reg_only=reg_only)
    return ARM_MOVE_DURATION_SEC


async def back_arm_left_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_ARM_LEFT, 0, reg_only=reg_only)
    return ARM_MOVE_DURATION_SEC


## BACK_ARM_RIGHT
async def back_arm_right_open(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_ARM_RIGHT, 0, reg_only=reg_only)
    return ARM_MOVE_DURATION_SEC


async def back_arm_right_close(planner: "Planner", reg_only: bool = False) -> float:
    planner.scservos.set(SCServoEnum.BACK_ARM_RIGHT, 0, reg_only=reg_only)
    return ARM_MOVE_DURATION_SEC


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
