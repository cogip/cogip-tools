from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
NOT_FOUND: PB_ParameterStatus
PARAM_TAG_ACCELERATION_LIMIT: PB_ParameterTag
PARAM_TAG_ANGULAR: PB_ParameterTag
PARAM_TAG_ENCODER: PB_ParameterTag
PARAM_TAG_INTEGRAL_LIMIT: PB_ParameterTag
PARAM_TAG_LINEAR: PB_ParameterTag
PARAM_TAG_LOCALIZATION: PB_ParameterTag
PARAM_TAG_NONE: PB_ParameterTag
PARAM_TAG_OTOS: PB_ParameterTag
PARAM_TAG_PID: PB_ParameterTag
PARAM_TAG_POLARITY: PB_ParameterTag
PARAM_TAG_POSE: PB_ParameterTag
PARAM_TAG_POSE_THRESHOLD: PB_ParameterTag
PARAM_TAG_QUADPID: PB_ParameterTag
PARAM_TAG_SPEED: PB_ParameterTag
PARAM_TAG_SPEED_LIMIT: PB_ParameterTag
PARAM_TAG_TRACKER: PB_ParameterTag
PARAM_TAG_WHEEL_GEOMETRY: PB_ParameterTag
PARAM_TYPE_BOOL: PB_ParameterType
PARAM_TYPE_DOUBLE: PB_ParameterType
PARAM_TYPE_FLOAT: PB_ParameterType
PARAM_TYPE_INT32: PB_ParameterType
PARAM_TYPE_INT64: PB_ParameterType
PARAM_TYPE_UINT32: PB_ParameterType
PARAM_TYPE_UINT64: PB_ParameterType
SUCCESS: PB_ParameterStatus
VALIDATION_FAILED: PB_ParameterStatus

class PB_ParameterAnnounceBounds(_message.Message):
    __slots__ = ["key_hash", "max_value", "min_value"]
    KEY_HASH_FIELD_NUMBER: _ClassVar[int]
    MAX_VALUE_FIELD_NUMBER: _ClassVar[int]
    MIN_VALUE_FIELD_NUMBER: _ClassVar[int]
    key_hash: int
    max_value: PB_ParameterValue
    min_value: PB_ParameterValue
    def __init__(self, key_hash: _Optional[int] = ..., min_value: _Optional[_Union[PB_ParameterValue, _Mapping]] = ..., max_value: _Optional[_Union[PB_ParameterValue, _Mapping]] = ...) -> None: ...

class PB_ParameterAnnounceHeader(_message.Message):
    __slots__ = ["board_id", "flags", "index", "key_hash", "tags_bitmask", "total_count", "type"]
    BOARD_ID_FIELD_NUMBER: _ClassVar[int]
    FLAGS_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    KEY_HASH_FIELD_NUMBER: _ClassVar[int]
    TAGS_BITMASK_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    board_id: int
    flags: int
    index: int
    key_hash: int
    tags_bitmask: int
    total_count: int
    type: PB_ParameterType
    def __init__(self, board_id: _Optional[int] = ..., key_hash: _Optional[int] = ..., type: _Optional[_Union[PB_ParameterType, str]] = ..., tags_bitmask: _Optional[int] = ..., flags: _Optional[int] = ..., total_count: _Optional[int] = ..., index: _Optional[int] = ...) -> None: ...

class PB_ParameterAnnounceName(_message.Message):
    __slots__ = ["key_hash", "name"]
    KEY_HASH_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    key_hash: int
    name: str
    def __init__(self, key_hash: _Optional[int] = ..., name: _Optional[str] = ...) -> None: ...

class PB_ParameterAnnounceRequest(_message.Message):
    __slots__ = ["tag_filter"]
    TAG_FILTER_FIELD_NUMBER: _ClassVar[int]
    tag_filter: PB_ParameterTag
    def __init__(self, tag_filter: _Optional[_Union[PB_ParameterTag, str]] = ...) -> None: ...

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

class PB_ParameterType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class PB_ParameterTag(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
