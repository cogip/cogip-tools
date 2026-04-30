from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class PB_SpeedOrder(_message.Message):
    __slots__ = ["angular_speed_deg_s", "duration_ms", "linear_speed_mm_s"]
    ANGULAR_SPEED_DEG_S_FIELD_NUMBER: _ClassVar[int]
    DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    LINEAR_SPEED_MM_S_FIELD_NUMBER: _ClassVar[int]
    angular_speed_deg_s: int
    duration_ms: int
    linear_speed_mm_s: int
    def __init__(self, linear_speed_mm_s: _Optional[int] = ..., angular_speed_deg_s: _Optional[int] = ..., duration_ms: _Optional[int] = ...) -> None: ...
