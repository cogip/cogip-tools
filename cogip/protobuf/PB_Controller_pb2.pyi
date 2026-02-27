from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PB_ControllerEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    QUADPID: _ClassVar[PB_ControllerEnum]
    LINEAR_POSE_DISABLED: _ClassVar[PB_ControllerEnum]
    QUADPID_TRACKER: _ClassVar[PB_ControllerEnum]
    LINEAR_SPEED_TUNING: _ClassVar[PB_ControllerEnum]
    ANGULAR_SPEED_TUNING: _ClassVar[PB_ControllerEnum]
    LINEAR_POSE_TUNING: _ClassVar[PB_ControllerEnum]
    ANGULAR_POSE_TUNING: _ClassVar[PB_ControllerEnum]
    LINEAR_POSE_TEST: _ClassVar[PB_ControllerEnum]
    ADAPTIVE_PURE_PURSUIT: _ClassVar[PB_ControllerEnum]
QUADPID: PB_ControllerEnum
LINEAR_POSE_DISABLED: PB_ControllerEnum
QUADPID_TRACKER: PB_ControllerEnum
LINEAR_SPEED_TUNING: PB_ControllerEnum
ANGULAR_SPEED_TUNING: PB_ControllerEnum
LINEAR_POSE_TUNING: PB_ControllerEnum
ANGULAR_POSE_TUNING: PB_ControllerEnum
LINEAR_POSE_TEST: PB_ControllerEnum
ADAPTIVE_PURE_PURSUIT: PB_ControllerEnum

class PB_Controller(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: PB_ControllerEnum
    def __init__(self, id: _Optional[_Union[PB_ControllerEnum, str]] = ...) -> None: ...
