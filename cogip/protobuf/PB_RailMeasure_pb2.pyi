from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class PB_RailMeasure(_message.Message):
    __slots__ = ["current_ma", "voltage_mv"]
    CURRENT_MA_FIELD_NUMBER: _ClassVar[int]
    VOLTAGE_MV_FIELD_NUMBER: _ClassVar[int]
    current_ma: int
    voltage_mv: int
    def __init__(self, voltage_mv: _Optional[int] = ..., current_ma: _Optional[int] = ...) -> None: ...
