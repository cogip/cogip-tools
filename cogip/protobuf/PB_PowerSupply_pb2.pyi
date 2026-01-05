from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class PB_PowerRailsStatus(_message.Message):
    __slots__ = ("p3V3_pgood", "p5V0_pgood", "p7V5_pgood", "pxVx_pgood")
    P3V3_PGOOD_FIELD_NUMBER: _ClassVar[int]
    P5V0_PGOOD_FIELD_NUMBER: _ClassVar[int]
    P7V5_PGOOD_FIELD_NUMBER: _ClassVar[int]
    PXVX_PGOOD_FIELD_NUMBER: _ClassVar[int]
    p3V3_pgood: bool
    p5V0_pgood: bool
    p7V5_pgood: bool
    pxVx_pgood: bool
    def __init__(self, p3V3_pgood: bool = ..., p5V0_pgood: bool = ..., p7V5_pgood: bool = ..., pxVx_pgood: bool = ...) -> None: ...

class PB_EmergencyStopStatus(_message.Message):
    __slots__ = ("emergency_stop",)
    EMERGENCY_STOP_FIELD_NUMBER: _ClassVar[int]
    emergency_stop: bool
    def __init__(self, emergency_stop: bool = ...) -> None: ...

class PB_PowerSourceStatus(_message.Message):
    __slots__ = ("battery_valid", "dc_supply_valid")
    BATTERY_VALID_FIELD_NUMBER: _ClassVar[int]
    DC_SUPPLY_VALID_FIELD_NUMBER: _ClassVar[int]
    battery_valid: bool
    dc_supply_valid: bool
    def __init__(self, battery_valid: bool = ..., dc_supply_valid: bool = ...) -> None: ...
