from typing import TYPE_CHECKING

from cogip.models.actuators import (
    PositionalActuatorCommand,
    PositionalActuatorEnum,
    ServoCommand,
    ServoEnum,
)

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
