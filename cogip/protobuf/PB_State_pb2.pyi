import PB_Polar_pb2 as _PB_Polar_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PB_State(_message.Message):
    __slots__ = ["cycle", "speed_current", "speed_order"]
    CYCLE_FIELD_NUMBER: _ClassVar[int]
    SPEED_CURRENT_FIELD_NUMBER: _ClassVar[int]
    SPEED_ORDER_FIELD_NUMBER: _ClassVar[int]
    cycle: int
    speed_current: _PB_Polar_pb2.PB_Polar
    speed_order: _PB_Polar_pb2.PB_Polar
    def __init__(self, cycle: _Optional[int] = ..., speed_current: _Optional[_Union[_PB_Polar_pb2.PB_Polar, _Mapping]] = ..., speed_order: _Optional[_Union[_PB_Polar_pb2.PB_Polar, _Mapping]] = ...) -> None: ...
