from enum import IntEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

from cogip.protobuf import PB_PositionalActuatorCommand

# Actuators common definitions


class ActuatorsKindEnum(IntEnum):
    """Enum defining actuators kind"""

    servo = 0
    positional_actuator = 1
    bool_sensor = 2


class ActuatorBase(BaseModel):
    """Base model for actuators"""

    enabled: bool = Field(
        False,
        title="Enabled",
        description="An actuator is enabled if it has been initialized with its current value",
    )


# Positional Actuators related definitions


class PositionalActuatorEnum(IntEnum):
    """Enum defining positional actuators IDs"""

    MOTOR_LIFT = 0


class PositionalActuatorCommand(BaseModel):
    """Model defining a command to send to positional actuators"""

    kind: Literal[ActuatorsKindEnum.positional_actuator] = ActuatorsKindEnum.positional_actuator
    id: PositionalActuatorEnum = Field(..., title="Id", description="Positional Actuator identifier")
    command: int = Field(
        0,
        ge=-100,
        le=999,
        title="Position Command",
        description="Current positional actuator position command",
    )
    speed: int = Field(
        100,
        ge=1,
        le=100,
        title="Speed",
        description="Speed",
    )
    timeout: int = Field(
        2000,
        ge=100,
        le=5000,
        title="Timeout",
        description="Timeout",
    )

    @field_validator("kind", mode="before")
    @classmethod
    def validate_kind(cls, v: str) -> ActuatorsKindEnum:
        try:
            value = ActuatorsKindEnum[v]
        except KeyError:
            try:
                value = ActuatorsKindEnum(v)
            except Exception:
                raise ValueError("Not a ActuatorsKindEnum")
        if value != ActuatorsKindEnum.positional_actuator:
            raise ValueError("Not ActuatorsKindEnum.positional_actuator value")
        return value

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, v: str) -> PositionalActuatorEnum:
        try:
            return PositionalActuatorEnum[v]
        except KeyError:
            try:
                return PositionalActuatorEnum(v)
            except Exception:
                raise ValueError("Not a PositionalActuatorEnum")

    def pb_copy(self, message: PB_PositionalActuatorCommand) -> None:
        """Copy values to Protobuf message"""
        message.id = self.id
        message.command = self.command
        message.speed = self.speed
        message.timeout = self.timeout


class PositionalActuator(ActuatorBase, PositionalActuatorCommand):
    "Full model for positional actuators"

    pass


# Bool sensor related definitions


class BoolSensorEnum(IntEnum):
    """Enum defining bool sensors IDs"""

    UNDEFINED = 0


class BoolSensor(BaseModel):
    """Model defining bool sensor state"""

    kind: Literal[ActuatorsKindEnum.bool_sensor] = ActuatorsKindEnum.bool_sensor
    id: Annotated[
        BoolSensorEnum,
        Field(
            title="Id",
            description="Bool sensor identifier",
        ),
    ]
    state: Annotated[
        bool,
        Field(
            title="State",
            description="Bool sensor state",
        ),
    ] = False


ActuatorState = PositionalActuator | BoolSensor
ActuatorCommand = PositionalActuatorCommand


# Actuator limits
actuator_limits: dict[IntEnum, tuple[int, int]] = {
    PositionalActuatorEnum.MOTOR_LIFT: (0, 150),
}
