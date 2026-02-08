from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

BLOCKED: PB_PositionalActuatorStateEnum
BOOL_SENSOR: PB_ActuatorsTypeEnum
DESCRIPTOR: _descriptor.FileDescriptor
INTERMEDIATE_REACHED: PB_PositionalActuatorStateEnum
MOTOR_LIFT_1: PB_PositionalActuatorEnum
MOTOR_LIFT_2: PB_PositionalActuatorEnum
NONE: PB_BoolSensorEnum
POSITIONAL: PB_ActuatorsTypeEnum
REACHED: PB_PositionalActuatorStateEnum
TIMEOUT: PB_PositionalActuatorStateEnum

class PB_ActuatorCommand(_message.Message):
    __slots__ = ["positional_actuator"]
    POSITIONAL_ACTUATOR_FIELD_NUMBER: _ClassVar[int]
    positional_actuator: PB_PositionalActuatorCommand
    def __init__(self, positional_actuator: _Optional[_Union[PB_PositionalActuatorCommand, _Mapping]] = ...) -> None: ...

class PB_ActuatorState(_message.Message):
    __slots__ = ["bool_sensor", "positional_actuator"]
    BOOL_SENSOR_FIELD_NUMBER: _ClassVar[int]
    POSITIONAL_ACTUATOR_FIELD_NUMBER: _ClassVar[int]
    bool_sensor: PB_BoolSensor
    positional_actuator: PB_PositionalActuator
    def __init__(self, positional_actuator: _Optional[_Union[PB_PositionalActuator, _Mapping]] = ..., bool_sensor: _Optional[_Union[PB_BoolSensor, _Mapping]] = ...) -> None: ...

class PB_BoolSensor(_message.Message):
    __slots__ = ["id", "state"]
    ID_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    id: PB_BoolSensorEnum
    state: bool
    def __init__(self, id: _Optional[_Union[PB_BoolSensorEnum, str]] = ..., state: bool = ...) -> None: ...

class PB_PositionalActuator(_message.Message):
    __slots__ = ["id", "position", "state"]
    ID_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    id: PB_PositionalActuatorEnum
    position: int
    state: PB_PositionalActuatorStateEnum
    def __init__(self, id: _Optional[_Union[PB_PositionalActuatorEnum, str]] = ..., state: _Optional[_Union[PB_PositionalActuatorStateEnum, str]] = ..., position: _Optional[int] = ...) -> None: ...

class PB_PositionalActuatorCommand(_message.Message):
    __slots__ = ["command", "id", "speed", "timeout"]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    command: int
    id: PB_PositionalActuatorEnum
    speed: int
    timeout: int
    def __init__(self, id: _Optional[_Union[PB_PositionalActuatorEnum, str]] = ..., command: _Optional[int] = ..., speed: _Optional[int] = ..., timeout: _Optional[int] = ...) -> None: ...

class PB_ActuatorsTypeEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class PB_PositionalActuatorEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class PB_BoolSensorEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class PB_PositionalActuatorStateEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
