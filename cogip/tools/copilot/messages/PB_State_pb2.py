# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: PB_State.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import PB_Mode_pb2 as PB__Mode__pb2
import PB_Polar_pb2 as PB__Polar__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='PB_State.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x0ePB_State.proto\x1a\rPB_Mode.proto\x1a\x0ePB_Polar.proto\"s\n\x08PB_State\x12\x16\n\x04mode\x18\x01 \x01(\x0e\x32\x08.PB_Mode\x12\r\n\x05\x63ycle\x18\x02 \x01(\r\x12 \n\rspeed_current\x18\x03 \x01(\x0b\x32\t.PB_Polar\x12\x1e\n\x0bspeed_order\x18\x04 \x01(\x0b\x32\t.PB_Polarb\x06proto3'
  ,
  dependencies=[PB__Mode__pb2.DESCRIPTOR,PB__Polar__pb2.DESCRIPTOR,])




_PB_STATE = _descriptor.Descriptor(
  name='PB_State',
  full_name='PB_State',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='mode', full_name='PB_State.mode', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='cycle', full_name='PB_State.cycle', index=1,
      number=2, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='speed_current', full_name='PB_State.speed_current', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='speed_order', full_name='PB_State.speed_order', index=3,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=49,
  serialized_end=164,
)

_PB_STATE.fields_by_name['mode'].enum_type = PB__Mode__pb2._PB_MODE
_PB_STATE.fields_by_name['speed_current'].message_type = PB__Polar__pb2._PB_POLAR
_PB_STATE.fields_by_name['speed_order'].message_type = PB__Polar__pb2._PB_POLAR
DESCRIPTOR.message_types_by_name['PB_State'] = _PB_STATE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

PB_State = _reflection.GeneratedProtocolMessageType('PB_State', (_message.Message,), {
  'DESCRIPTOR' : _PB_STATE,
  '__module__' : 'PB_State_pb2'
  # @@protoc_insertion_point(class_scope:PB_State)
  })
_sym_db.RegisterMessage(PB_State)


# @@protoc_insertion_point(module_scope)
