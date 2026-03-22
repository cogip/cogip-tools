from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

ANGULAR_POSE_PID: PB_PidEnum
ANGULAR_SPEED_PID: PB_PidEnum
DESCRIPTOR: _descriptor.FileDescriptor
LINEAR_POSE_PID: PB_PidEnum
LINEAR_SPEED_PID: PB_PidEnum

class PB_PidEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
