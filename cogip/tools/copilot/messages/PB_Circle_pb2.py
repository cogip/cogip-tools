# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: PB_Circle.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='PB_Circle.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\x0fPB_Circle.proto\"1\n\tPB_Circle\x12\t\n\x01x\x18\x01 \x01(\x11\x12\t\n\x01y\x18\x02 \x01(\x11\x12\x0e\n\x06radius\x18\x03 \x01(\rb\x06proto3')
)




_PB_CIRCLE = _descriptor.Descriptor(
  name='PB_Circle',
  full_name='PB_Circle',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='x', full_name='PB_Circle.x', index=0,
      number=1, type=17, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='y', full_name='PB_Circle.y', index=1,
      number=2, type=17, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='radius', full_name='PB_Circle.radius', index=2,
      number=3, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
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
  serialized_start=19,
  serialized_end=68,
)

DESCRIPTOR.message_types_by_name['PB_Circle'] = _PB_CIRCLE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

PB_Circle = _reflection.GeneratedProtocolMessageType('PB_Circle', (_message.Message,), dict(
  DESCRIPTOR = _PB_CIRCLE,
  __module__ = 'PB_Circle_pb2'
  # @@protoc_insertion_point(class_scope:PB_Circle)
  ))
_sym_db.RegisterMessage(PB_Circle)


# @@protoc_insertion_point(module_scope)
