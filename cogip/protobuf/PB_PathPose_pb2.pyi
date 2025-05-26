import PB_Pose_pb2 as _PB_Pose_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PB_PathPose(_message.Message):
    __slots__ = ["allow_reverse", "bypass_anti_blocking", "bypass_final_orientation", "is_intermediate", "max_speed_ratio_angular", "max_speed_ratio_linear", "pose", "timeout_ms"]
    ALLOW_REVERSE_FIELD_NUMBER: _ClassVar[int]
    BYPASS_ANTI_BLOCKING_FIELD_NUMBER: _ClassVar[int]
    BYPASS_FINAL_ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    IS_INTERMEDIATE_FIELD_NUMBER: _ClassVar[int]
    MAX_SPEED_RATIO_ANGULAR_FIELD_NUMBER: _ClassVar[int]
    MAX_SPEED_RATIO_LINEAR_FIELD_NUMBER: _ClassVar[int]
    POSE_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_MS_FIELD_NUMBER: _ClassVar[int]
    allow_reverse: bool
    bypass_anti_blocking: bool
    bypass_final_orientation: bool
    is_intermediate: bool
    max_speed_ratio_angular: int
    max_speed_ratio_linear: int
    pose: _PB_Pose_pb2.PB_Pose
    timeout_ms: int
    def __init__(self, pose: _Optional[_Union[_PB_Pose_pb2.PB_Pose, _Mapping]] = ..., max_speed_ratio_linear: _Optional[int] = ..., max_speed_ratio_angular: _Optional[int] = ..., allow_reverse: bool = ..., bypass_anti_blocking: bool = ..., timeout_ms: _Optional[int] = ..., bypass_final_orientation: bool = ..., is_intermediate: bool = ...) -> None: ...
