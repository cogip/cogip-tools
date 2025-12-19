from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PB_ActuatorsTypeEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    POSITIONAL: _ClassVar[PB_ActuatorsTypeEnum]
    BOOL_SENSOR: _ClassVar[PB_ActuatorsTypeEnum]

class PB_PositionalActuatorEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MOTOR_LIFT: _ClassVar[PB_PositionalActuatorEnum]

class PB_BoolSensorEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NONE: _ClassVar[PB_BoolSensorEnum]

class PB_PositionalActuatorStateEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    REACHED: _ClassVar[PB_PositionalActuatorStateEnum]
    INTERMEDIATE_REACHED: _ClassVar[PB_PositionalActuatorStateEnum]
    TIMEOUT: _ClassVar[PB_PositionalActuatorStateEnum]
    BLOCKED: _ClassVar[PB_PositionalActuatorStateEnum]
POSITIONAL: PB_ActuatorsTypeEnum
BOOL_SENSOR: PB_ActuatorsTypeEnum
MOTOR_LIFT: PB_PositionalActuatorEnum
NONE: PB_BoolSensorEnum
REACHED: PB_PositionalActuatorStateEnum
INTERMEDIATE_REACHED: PB_PositionalActuatorStateEnum
TIMEOUT: PB_PositionalActuatorStateEnum
BLOCKED: PB_PositionalActuatorStateEnum

class PB_PositionalActuator(_message.Message):
    __slots__ = ("id", "state", "position")
    ID_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    id: PB_PositionalActuatorEnum
    state: PB_PositionalActuatorStateEnum
    position: int
    def __init__(self, id: _Optional[_Union[PB_PositionalActuatorEnum, str]] = ..., state: _Optional[_Union[PB_PositionalActuatorStateEnum, str]] = ..., position: _Optional[int] = ...) -> None: ...

class PB_BoolSensor(_message.Message):
    __slots__ = ("id", "state")
    ID_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    id: PB_BoolSensorEnum
    state: bool
    def __init__(self, id: _Optional[_Union[PB_BoolSensorEnum, str]] = ..., state: bool = ...) -> None: ...

class PB_ActuatorState(_message.Message):
    __slots__ = ("positional_actuator", "bool_sensor")
    POSITIONAL_ACTUATOR_FIELD_NUMBER: _ClassVar[int]
    BOOL_SENSOR_FIELD_NUMBER: _ClassVar[int]
    positional_actuator: PB_PositionalActuator
    bool_sensor: PB_BoolSensor
    def __init__(self, positional_actuator: _Optional[_Union[PB_PositionalActuator, _Mapping]] = ..., bool_sensor: _Optional[_Union[PB_BoolSensor, _Mapping]] = ...) -> None: ...

class PB_PositionalActuatorCommand(_message.Message):
    __slots__ = ("id", "command", "speed", "timeout")
    ID_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    id: PB_PositionalActuatorEnum
    command: int
    speed: int
    timeout: int
    def __init__(self, id: _Optional[_Union[PB_PositionalActuatorEnum, str]] = ..., command: _Optional[int] = ..., speed: _Optional[int] = ..., timeout: _Optional[int] = ...) -> None: ...

class PB_ActuatorCommand(_message.Message):
    __slots__ = ("positional_actuator",)
    POSITIONAL_ACTUATOR_FIELD_NUMBER: _ClassVar[int]
    positional_actuator: PB_PositionalActuatorCommand
    def __init__(self, positional_actuator: _Optional[_Union[PB_PositionalActuatorCommand, _Mapping]] = ...) -> None: ...
