from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class PB_Polar(_message.Message):
    __slots__ = ["angle", "distance"]
    ANGLE_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_FIELD_NUMBER: _ClassVar[int]
    angle: int
    distance: int
    def __init__(self, distance: _Optional[int] = ..., angle: _Optional[int] = ...) -> None: ...
