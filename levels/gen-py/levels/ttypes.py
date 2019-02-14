#
# Autogenerated by Thrift Compiler (0.12.0)
#
# DO NOT EDIT UNLESS YOU ARE SURE THAT YOU KNOW WHAT YOU ARE DOING
#
#  options string: py
#

from thrift.Thrift import TType, TMessageType, TFrozenDict, TException, TApplicationException
from thrift.protocol.TProtocol import TProtocolException
from thrift.TRecursive import fix_spec

import sys

from thrift.transport import TTransport
all_structs = []


class can_levels(object):
    """
    Attributes:
     - count
     - can_levels

    """


    def __init__(self, count=None, can_levels=None,):
        self.count = count
        self.can_levels = can_levels

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None:
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I32:
                    self.count = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.MAP:
                    self.can_levels = {}
                    (_ktype1, _vtype2, _size0) = iprot.readMapBegin()
                    for _i4 in range(_size0):
                        _key5 = iprot.readI64()
                        _val6 = iprot.readDouble()
                        self.can_levels[_key5] = _val6
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('can_levels')
        if self.count is not None:
            oprot.writeFieldBegin('count', TType.I32, 1)
            oprot.writeI32(self.count)
            oprot.writeFieldEnd()
        if self.can_levels is not None:
            oprot.writeFieldBegin('can_levels', TType.MAP, 2)
            oprot.writeMapBegin(TType.I64, TType.DOUBLE, len(self.can_levels))
            for kiter7, viter8 in self.can_levels.items():
                oprot.writeI64(kiter7)
                oprot.writeDouble(viter8)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)
all_structs.append(can_levels)
can_levels.thrift_spec = (
    None,  # 0
    (1, TType.I32, 'count', None, None, ),  # 1
    (2, TType.MAP, 'can_levels', (TType.I64, None, TType.DOUBLE, None, False), None, ),  # 2
)
fix_spec(all_structs)
del all_structs