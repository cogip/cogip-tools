from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class PB_PidEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    LINEAR_POSE_PID: _ClassVar[PB_PidEnum]
    ANGULAR_POSE_PID: _ClassVar[PB_PidEnum]
    LINEAR_SPEED_PID: _ClassVar[PB_PidEnum]
    ANGULAR_SPEED_PID: _ClassVar[PB_PidEnum]
LINEAR_POSE_PID: PB_PidEnum
ANGULAR_POSE_PID: PB_PidEnum
LINEAR_SPEED_PID: PB_PidEnum
ANGULAR_SPEED_PID: PB_PidEnum
