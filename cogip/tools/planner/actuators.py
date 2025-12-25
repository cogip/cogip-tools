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


async def lift_0(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT, 0, speed)
    return 0


async def lift_5(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT, 5, speed)
    return 0


async def lift_125(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT, 125, speed)
    return 0


async def lift_140(planner: "Planner", speed: int = 100) -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_LIFT, 140, speed)
    return 0
