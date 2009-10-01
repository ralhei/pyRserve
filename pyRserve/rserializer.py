import struct, sys, cStringIO, datetime
from binascii import hexlify, unhexlify
###
import rtypes
from misc import FunctionMapper

DEBUG = False

class RSerializer(object):
    #
    serializeMap = {}
    fmap = FunctionMapper(serializeMap)
    #
    def __init__(self, fp=None):
        self._orig_fp = fp
        if fp:
            # check that file is seekable: (sockets are not seekable!)
            assert hasattr(fp, 'seek')
        self._fp = fp or cStringIO.StringIO()

    def serialize(self, o):
        if isinstance(self._fp, cStringIO.OutputType) and self._fp is not self._orig_fp:
            # remove all preexisting data from internal cStringIO buffer
            self._fp.truncate()

        self._writeHeader()
        self._serialize(o)
        self._finalizeHeader()
        # If 'fp' was None before, just return the result as a string, otherwise nothing is returned
        # (because the data has been written to the file provided by 'fp')
        if not self._orig_fp:
            data = self._fp.getvalue()
            return data

    def _writeHeader(self):
        # Depending on whether we send a failure or not cmd_resp has to be set (for now no failure!!)
        resp_cmd = rtypes.CMD_eval
        # Set length to zero initially, will be fixed in _finalizerHeader() when msg size is determined:
        msg_length_lower = msg_length_higher = 0
        data_offset = 0
        header = struct.pack('<IIII', resp_cmd, msg_length_lower, data_offset, msg_length_higher)
        if DEBUG:
            print 'Writing header: %d bytes: %s' % (len(header), repr(header))
        self._fp.write(header)

    def _finalizeHeader(self):
        # and finally we correctly set the length of the entire data package (in bytes) minus header size:
        dataSize = self._fp.tell() - rtypes.RHEADER_SIZE
        # TODO: Also handle data larger than 2*32 (user upper part of message length!!)
        assert dataSize < 2*32, 'data larger than 2*32 not yet implemented'
        self._fp.seek(4)
        if DEBUG:
            print 'writing size of header: %2d' % dataSize
        self._fp.write(struct.pack('<I', dataSize))

    def _serialize(self, o):
        s_func = self.serializeMap[type(o)]
        s_func(self, o)
    
    @fmap(str)
    def s_string_or_symbol(self, o):
        l = len(o)
        # The string packet contains trailing padding zeros to make it always a multiple of 4 in length:
        multi4Len = l + (4-divmod(l, 4)[1])
        # send data:
        stringHeader = struct.pack('B', rtypes.DT_STRING) + struct.pack('<i', multi4Len)[:3]
        data = stringHeader + o + (multi4Len-l)*'\x00'
        if DEBUG:
            print 'Writing string: %2d bytes: %s' % (len(data), repr(data))
        self._fp.write(data)


def rserialize(o, fp=None, **kw):
    rser = RSerializer(fp=fp)
    return rser.serialize(o, **kw)


if __name__ == '__main__':
    print repr(rserialize('1'))
