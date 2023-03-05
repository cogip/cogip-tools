# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: PB_Pid.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import PB_PidEnum_pb2 as PB__PidEnum__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='PB_Pid.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x0cPB_Pid.proto\x1a\x10PB_PidEnum.proto\"\x91\x01\n\x06PB_Pid\x12\x17\n\x02id\x18\x01 \x01(\x0e\x32\x0b.PB_PidEnum\x12\n\n\x02kp\x18\x02 \x01(\x01\x12\n\n\x02ki\x18\x03 \x01(\x01\x12\n\n\x02kd\x18\x04 \x01(\x01\x12\x16\n\x0eprevious_error\x18\x05 \x01(\x01\x12\x15\n\rintegral_term\x18\x06 \x01(\x01\x12\x1b\n\x13integral_term_limit\x18\x07 \x01(\x01\" \n\x07PB_Pids\x12\x15\n\x04pids\x18\x01 \x03(\x0b\x32\x07.PB_Pidb\x06proto3'
  ,
  dependencies=[PB__PidEnum__pb2.DESCRIPTOR,])




_PB_PID = _descriptor.Descriptor(
  name='PB_Pid',
  full_name='PB_Pid',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='PB_Pid.id', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='kp', full_name='PB_Pid.kp', index=1,
      number=2, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='ki', full_name='PB_Pid.ki', index=2,
      number=3, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='kd', full_name='PB_Pid.kd', index=3,
      number=4, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='previous_error', full_name='PB_Pid.previous_error', index=4,
      number=5, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='integral_term', full_name='PB_Pid.integral_term', index=5,
      number=6, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='integral_term_limit', full_name='PB_Pid.integral_term_limit', index=6,
      number=7, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
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
  serialized_start=35,
  serialized_end=180,
)


_PB_PIDS = _descriptor.Descriptor(
  name='PB_Pids',
  full_name='PB_Pids',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='pids', full_name='PB_Pids.pids', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
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
  serialized_start=182,
  serialized_end=214,
)

_PB_PID.fields_by_name['id'].enum_type = PB__PidEnum__pb2._PB_PIDENUM
_PB_PIDS.fields_by_name['pids'].message_type = _PB_PID
DESCRIPTOR.message_types_by_name['PB_Pid'] = _PB_PID
DESCRIPTOR.message_types_by_name['PB_Pids'] = _PB_PIDS
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

PB_Pid = _reflection.GeneratedProtocolMessageType('PB_Pid', (_message.Message,), {
  'DESCRIPTOR' : _PB_PID,
  '__module__' : 'PB_Pid_pb2'
  # @@protoc_insertion_point(class_scope:PB_Pid)
  })
_sym_db.RegisterMessage(PB_Pid)

PB_Pids = _reflection.GeneratedProtocolMessageType('PB_Pids', (_message.Message,), {
  'DESCRIPTOR' : _PB_PIDS,
  '__module__' : 'PB_Pid_pb2'
  # @@protoc_insertion_point(class_scope:PB_Pids)
  })
_sym_db.RegisterMessage(PB_Pids)


# @@protoc_insertion_point(module_scope)