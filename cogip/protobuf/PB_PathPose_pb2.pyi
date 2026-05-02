import PB_Pose_pb2 as _PB_Pose_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PB_MotionDirection(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BIDIRECTIONAL: _ClassVar[PB_MotionDirection]
    FORWARD_ONLY: _ClassVar[PB_MotionDirection]
    BACKWARD_ONLY: _ClassVar[PB_MotionDirection]
BIDIRECTIONAL: PB_MotionDirection
FORWARD_ONLY: PB_MotionDirection
BACKWARD_ONLY: PB_MotionDirection

class PB_PathPose(_message.Message):
    __slots__ = ("pose", "max_speed_ratio_linear", "max_speed_ratio_angular", "motion_direction", "bypass_anti_blocking", "timeout_ms", "bypass_final_orientation", "is_intermediate")
    POSE_FIELD_NUMBER: _ClassVar[int]
    MAX_SPEED_RATIO_LINEAR_FIELD_NUMBER: _ClassVar[int]
    MAX_SPEED_RATIO_ANGULAR_FIELD_NUMBER: _ClassVar[int]
    MOTION_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    BYPASS_ANTI_BLOCKING_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_MS_FIELD_NUMBER: _ClassVar[int]
    BYPASS_FINAL_ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    IS_INTERMEDIATE_FIELD_NUMBER: _ClassVar[int]
    pose: _PB_Pose_pb2.PB_Pose
    max_speed_ratio_linear: int
    max_speed_ratio_angular: int
    motion_direction: PB_MotionDirection
    bypass_anti_blocking: bool
    timeout_ms: int
    bypass_final_orientation: bool
    is_intermediate: bool
    def __init__(self, pose: _Optional[_Union[_PB_Pose_pb2.PB_Pose, _Mapping]] = ..., max_speed_ratio_linear: _Optional[int] = ..., max_speed_ratio_angular: _Optional[int] = ..., motion_direction: _Optional[_Union[PB_MotionDirection, str]] = ..., bypass_anti_blocking: bool = ..., timeout_ms: _Optional[int] = ..., bypass_final_orientation: bool = ..., is_intermediate: bool = ...) -> None: ...
