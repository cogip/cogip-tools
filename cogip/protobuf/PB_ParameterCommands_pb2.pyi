from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
NOT_FOUND: PB_ParameterStatus
SUCCESS: PB_ParameterStatus
VALIDATION_FAILED: PB_ParameterStatus

class PB_ParameterGetRequest(_message.Message):
    __slots__ = ["key_hash"]
    KEY_HASH_FIELD_NUMBER: _ClassVar[int]
    key_hash: int
    def __init__(self, key_hash: _Optional[int] = ...) -> None: ...

class PB_ParameterGetResponse(_message.Message):
    __slots__ = ["key_hash", "value"]
    KEY_HASH_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key_hash: int
    value: PB_ParameterValue
    def __init__(self, key_hash: _Optional[int] = ..., value: _Optional[_Union[PB_ParameterValue, _Mapping]] = ...) -> None: ...

class PB_ParameterSetRequest(_message.Message):
    __slots__ = ["key_hash", "value"]
    KEY_HASH_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key_hash: int
    value: PB_ParameterValue
    def __init__(self, key_hash: _Optional[int] = ..., value: _Optional[_Union[PB_ParameterValue, _Mapping]] = ...) -> None: ...

class PB_ParameterSetResponse(_message.Message):
    __slots__ = ["key_hash", "status"]
    KEY_HASH_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    key_hash: int
    status: PB_ParameterStatus
    def __init__(self, key_hash: _Optional[int] = ..., status: _Optional[_Union[PB_ParameterStatus, str]] = ...) -> None: ...

class PB_ParameterValue(_message.Message):
    __slots__ = ["bool_value", "double_value", "float_value", "int32_value", "int64_value", "uint32_value", "uint64_value"]
    BOOL_VALUE_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_VALUE_FIELD_NUMBER: _ClassVar[int]
    FLOAT_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT32_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT64_VALUE_FIELD_NUMBER: _ClassVar[int]
    UINT32_VALUE_FIELD_NUMBER: _ClassVar[int]
    UINT64_VALUE_FIELD_NUMBER: _ClassVar[int]
    bool_value: bool
    double_value: float
    float_value: float
    int32_value: int
    int64_value: int
    uint32_value: int
    uint64_value: int
    def __init__(self, float_value: _Optional[float] = ..., double_value: _Optional[float] = ..., int32_value: _Optional[int] = ..., uint32_value: _Optional[int] = ..., int64_value: _Optional[int] = ..., uint64_value: _Optional[int] = ..., bool_value: bool = ...) -> None: ...

class PB_ParameterStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
