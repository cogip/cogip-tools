import PB_PidEnum_pb2 as _PB_PidEnum_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PB_Pid(_message.Message):
    __slots__ = ("id", "kp", "ki", "kd", "previous_error", "integral_term", "integral_term_limit")
    ID_FIELD_NUMBER: _ClassVar[int]
    KP_FIELD_NUMBER: _ClassVar[int]
    KI_FIELD_NUMBER: _ClassVar[int]
    KD_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_ERROR_FIELD_NUMBER: _ClassVar[int]
    INTEGRAL_TERM_FIELD_NUMBER: _ClassVar[int]
    INTEGRAL_TERM_LIMIT_FIELD_NUMBER: _ClassVar[int]
    id: _PB_PidEnum_pb2.PB_PidEnum
    kp: float
    ki: float
    kd: float
    previous_error: float
    integral_term: float
    integral_term_limit: float
    def __init__(self, id: _Optional[_Union[_PB_PidEnum_pb2.PB_PidEnum, str]] = ..., kp: _Optional[float] = ..., ki: _Optional[float] = ..., kd: _Optional[float] = ..., previous_error: _Optional[float] = ..., integral_term: _Optional[float] = ..., integral_term_limit: _Optional[float] = ...) -> None: ...

class PB_Pid_Id(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: _PB_PidEnum_pb2.PB_PidEnum
    def __init__(self, id: _Optional[_Union[_PB_PidEnum_pb2.PB_PidEnum, str]] = ...) -> None: ...
