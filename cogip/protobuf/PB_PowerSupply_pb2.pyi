import PB_RailMeasure_pb2 as _PB_RailMeasure_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PB_PowerRailsMeasures(_message.Message):
    __slots__ = ["p12V0", "p3V3", "p5V0", "p7V5", "pxVx"]
    P12V0_FIELD_NUMBER: _ClassVar[int]
    P3V3_FIELD_NUMBER: _ClassVar[int]
    P5V0_FIELD_NUMBER: _ClassVar[int]
    P7V5_FIELD_NUMBER: _ClassVar[int]
    PXVX_FIELD_NUMBER: _ClassVar[int]
    p12V0: _PB_RailMeasure_pb2.PB_RailMeasure
    p3V3: _PB_RailMeasure_pb2.PB_RailMeasure
    p5V0: _PB_RailMeasure_pb2.PB_RailMeasure
    p7V5: _PB_RailMeasure_pb2.PB_RailMeasure
    pxVx: _PB_RailMeasure_pb2.PB_RailMeasure
    def __init__(self, p3V3: _Optional[_Union[_PB_RailMeasure_pb2.PB_RailMeasure, _Mapping]] = ..., p5V0: _Optional[_Union[_PB_RailMeasure_pb2.PB_RailMeasure, _Mapping]] = ..., p7V5: _Optional[_Union[_PB_RailMeasure_pb2.PB_RailMeasure, _Mapping]] = ..., pxVx: _Optional[_Union[_PB_RailMeasure_pb2.PB_RailMeasure, _Mapping]] = ..., p12V0: _Optional[_Union[_PB_RailMeasure_pb2.PB_RailMeasure, _Mapping]] = ...) -> None: ...

class PB_PowerRailsStatus(_message.Message):
    __slots__ = ["p3V3_pgood", "p5V0_pgood", "p7V5_pgood", "pxVx_pgood"]
    P3V3_PGOOD_FIELD_NUMBER: _ClassVar[int]
    P5V0_PGOOD_FIELD_NUMBER: _ClassVar[int]
    P7V5_PGOOD_FIELD_NUMBER: _ClassVar[int]
    PXVX_PGOOD_FIELD_NUMBER: _ClassVar[int]
    p3V3_pgood: bool
    p5V0_pgood: bool
    p7V5_pgood: bool
    pxVx_pgood: bool
    def __init__(self, p3V3_pgood: bool = ..., p5V0_pgood: bool = ..., p7V5_pgood: bool = ..., pxVx_pgood: bool = ...) -> None: ...

class PB_PowerSourceStatus(_message.Message):
    __slots__ = ["battery_valid", "dc_supply_valid"]
    BATTERY_VALID_FIELD_NUMBER: _ClassVar[int]
    DC_SUPPLY_VALID_FIELD_NUMBER: _ClassVar[int]
    battery_valid: bool
    dc_supply_valid: bool
    def __init__(self, battery_valid: bool = ..., dc_supply_valid: bool = ...) -> None: ...
