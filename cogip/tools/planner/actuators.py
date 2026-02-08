from typing import TYPE_CHECKING

from cogip.models.actuators import (
    PositionalActuatorCommand,
    PositionalActuatorEnum,
)

if TYPE_CHECKING:
    from cogip.tools.planner.planner import Planner


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


# Lift 1 commands (10mm increments)
async def lift1_0(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_1, 0, speed)
    return 0


async def lift1_10(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_1, 10, speed)
    return 0


async def lift1_20(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_1, 20, speed)
    return 0


async def lift1_30(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_1, 30, speed)
    return 0


async def lift1_40(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_1, 40, speed)
    return 0


async def lift1_50(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_1, 50, speed)
    return 0


async def lift1_60(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_1, 60, speed)
    return 0


async def lift1_70(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_1, 70, speed)
    return 0


async def lift1_80(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_1, 80, speed)
    return 0


async def lift1_90(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_1, 90, speed)
    return 0


async def lift1_100(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_1, 100, speed)
    return 0


async def lift1_110(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_1, 110, speed)
    return 0


async def lift1_command(planner: "Planner", position: int, speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_1, position, speed)
    return 0


# Lift 2 commands (10mm increments)
async def lift2_0(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_2, 0, speed)
    return 0


async def lift2_10(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_2, 10, speed)
    return 0


async def lift2_20(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_2, 20, speed)
    return 0


async def lift2_30(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_2, 30, speed)
    return 0


async def lift2_40(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_2, 40, speed)
    return 0


async def lift2_50(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_2, 50, speed)
    return 0


async def lift2_60(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_2, 60, speed)
    return 0


async def lift2_70(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_2, 70, speed)
    return 0


async def lift2_80(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_2, 80, speed)
    return 0


async def lift2_90(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_2, 90, speed)
    return 0


async def lift2_100(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_2, 100, speed)
    return 0


async def lift2_110(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_2, 110, speed)
    return 0


async def lift2_command(planner: "Planner", position: int, speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT_2, position, speed)
    return 0
