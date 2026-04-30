from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class PB_TelemetryData(_message.Message):
    __slots__ = ["float_value", "int32_value", "int64_value", "key_hash", "timestamp_ms", "uint32_value", "uint64_value"]
    FLOAT_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT32_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT64_VALUE_FIELD_NUMBER: _ClassVar[int]
    KEY_HASH_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    UINT32_VALUE_FIELD_NUMBER: _ClassVar[int]
    UINT64_VALUE_FIELD_NUMBER: _ClassVar[int]
    float_value: float
    int32_value: int
    int64_value: int
    key_hash: int
    timestamp_ms: int
    uint32_value: int
    uint64_value: int
    def __init__(self, key_hash: _Optional[int] = ..., timestamp_ms: _Optional[int] = ..., float_value: _Optional[float] = ..., int32_value: _Optional[int] = ..., uint32_value: _Optional[int] = ..., int64_value: _Optional[int] = ..., uint64_value: _Optional[int] = ...) -> None: ...
