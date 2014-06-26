"""
Serializer class to convert Python objects into a binary data stream for
sending them to Rserve.
"""
__all__ = ['reval', 'rassign', 'rSerializeResponse', 'rShutdown']

import struct
import os
import socket
import io
import sys
import types
###
import numpy
###
from . import rtypes
from .misc import PY3, FunctionMapper, byteEncode, padLen4, string2bytesPad4
from .taggedContainers import TaggedList, TaggedArray

# turn on DEBUG to see extra information about what the serializer is
# doing with your data
DEBUG = 0


if PY3:
    # types.NoneType unfortunately does not exist in Python, so create it:
    NoneType = type(None)
    # make test work with Python 3 where 'long'-type does not exist:
    long = int
else:
    NoneType = types.NoneType


class RSerializer(object):
    """
    Class to to serialize Python objects into a binary data stream for sending
    them to Rserve.

    Depending on 'commandType' given to __init__ the resulting binary string
    can be used to send a command, to assign a variable in Rserve, or to
    reply to a request received from Rserve.
    """
    serializeMap = {}
    fmap = FunctionMapper(serializeMap)

    def __init__(self, commandType, fp=None):
        if isinstance(fp, socket.socket):
            # kwargs = {'mode': 'b'} if PY3 else {}
            self._orig_fp = fp  # fp.makefile(**kwargs)
            self._fp = io.BytesIO()
        elif not fp:
            self._fp = fp or io.BytesIO()
            self._orig_fp = None
        else:
            self._fp = self._orig_fp = fp
        self._dataSize = 0
        self._writeHeader(commandType)

    def _getRetVal(self):
        if self._orig_fp is self._fp:
            return None
        elif not self._orig_fp:
            return self._fp.getvalue()
        else:
            # i.e. socket: write result of _fp into socket-fp
            self._orig_fp.send(self._fp.getvalue())
            #self._orig_fp.flush()
            return None

    def _writeHeader(self, commandType):
        # Set length to zero initially, will be fixed in _finalizerHeader()
        # when msg size is determined:
        msg_length_lower = msg_length_higher = 0
        data_offset = 0
        header = struct.pack('<IIII', commandType, msg_length_lower,
                             data_offset, msg_length_higher)
        if DEBUG:
            print('Writing header: %d bytes: %s' % (len(header), repr(header)))
        self._fp.write(header)

    def finalize(self):
        # and finally we correctly set the length of the entire data package
        # (in bytes) minus header size:
        # dataSize = self._fp.tell() - rtypes.RHEADER_SIZE
        # TODO: Also handle data larger than 2**32
        # (use upper part of message length!!)
        assert self._dataSize < 2**32, \
            'data larger than 2**32 not yet implemented'
        self._fp.seek(4)
        if DEBUG:
            print('writing size of header: %2d' % self._dataSize)
        self._fp.write(struct.pack('<I', self._dataSize))
        return self._getRetVal()

    def _writeDataHeader(self, rTypeCode, length):
        """
        A data header consists of 4 bytes:
        [1]   rTypeCode
        [2-4] length of data block (3 bytes!!!)
        """
        self._fp.write(struct.pack('<Bi', rTypeCode, length)[:4])

    def serialize(self, o, dtTypeCode=rtypes.DT_SEXP):
        # Here the data typecode (DT_* ) of the entire message is written,
        # with its length. Then the actual data itself is written out.
        if dtTypeCode == rtypes.DT_STRING:
            paddedString = string2bytesPad4(o)
            length = len(paddedString)
            self._writeDataHeader(dtTypeCode, length)
            self._fp.write(paddedString)
        elif dtTypeCode == rtypes.DT_INT:
            length = 4
            self._writeDataHeader(dtTypeCode, length)
            self._fp.write(struct.pack('<i', o))
        elif dtTypeCode == rtypes.DT_SEXP:
            startPos = self._fp.tell()
            self._fp.write(b'\0\0\0\0')
            length = self.serializeExpr(o)
            self._fp.seek(startPos)
            self._writeDataHeader(dtTypeCode, length)
        else:
            raise NotImplementedError('no support for DT-type %x' % dtTypeCode)
        self._dataSize += length + 4

    def serializeExpr(self, o):
        if isinstance(o, numpy.ndarray):
            rTypeCode = rtypes.numpyMap[o.dtype.type]
        else:
            rTypeCode = type(o)
        try:
            s_func = self.serializeMap[rTypeCode]
        except KeyError:
            raise NotImplementedError('Serialization of "%s" not implemented' %
                                      rTypeCode)
        startPos = self._fp.tell()
        if DEBUG:
            print('Serializing expr %r with rTypeCode=%s using function %s' %
                  (o, rTypeCode, s_func))
        s_func(self, o)
        # determine and return the length of actual R expression data:
        return self._fp.tell() - startPos

    @fmap(NoneType, rtypes.XT_NULL)
    def s_null(self, o):
        """Send Python's None to R, resulting in NULL there"""
        # For NULL only the header needs to be written, there is no data body.
        self._writeDataHeader(rtypes.XT_NULL, 4)

    @fmap(rtypes.XT_STR, rtypes.XT_SYMNAME)
    def s_string_or_symbol(self, o, rTypeCode=rtypes.XT_STR):
        """
        Possible rTypeCodes for a given string are:
        - XT_STR
        - XT_SYMNAME
        """
        # The string packet contains trailing padding zeros to make it always
        # a multiple of 4 in length:
        paddedString = string2bytesPad4(o)
        length = len(paddedString)
        self._writeDataHeader(rTypeCode, length)
        if DEBUG:
            print('Writing string: %2d bytes: %s' %
                  (length, repr(paddedString)))
        self._fp.write(paddedString)

    ################ Arrays #########################################

    def __s_write_xt_array_tag_data(self, o):
        """
        Write tag data of an array, like dimension for a multi-dim array,
        or other information found. Return appropriate rTypeCode.
        """
        xt_tag_list = []
        if o.ndim > 1:
            xt_tag_list.append((b'dim', numpy.array(o.shape, numpy.int32)))
        if isinstance(o, TaggedArray):
            xt_tag_list.append((b'names', numpy.array(o.attr)))

        attrFlag = rtypes.XT_HAS_ATTR if xt_tag_list else 0
        rTypeCode = rtypes.numpyMap[o.dtype.type] | attrFlag
        # write length of zero for now, will be corrected later:
        self._writeDataHeader(rTypeCode, 0)
        if attrFlag:
            self.s_xt_tag_list(xt_tag_list)
        return rTypeCode

    def __s_update_xt_array_header(self, headerPos, rTypeCode):
        """
        Update length information of xt array header which has been
        previously temporarily set to 0 in __s_write_xt_array_tag_data()
        @arg headerPos: file position where header information should be
                        written.
        @arg rTypeCode
        """
        # subtract length of header (4 bytes), does not count to payload!
        length = self._fp.tell() - headerPos - 4
        self._fp.seek(headerPos)
        self._writeDataHeader(rTypeCode, length)
        self._fp.seek(0, os.SEEK_END)

    @fmap(*rtypes.STRING_TYPES)
    def s_xt_array_str(self, o):
        """Serialize single string object"""
        arr = numpy.array([o])
        self.s_xt_array_str(arr)

    @fmap(rtypes.XT_ARRAY_STR)
    def s_xt_array_str(self, o):
        """Serialize array of strings"""
        startPos = self._fp.tell()
        rTypeCode = self.__s_write_xt_array_tag_data(o)

        # reshape into 1d array:
        o1d = o.reshape(o.size, order='F')
        # Byte-encode them:
        bo = [byteEncode(d) for d in o1d]
        # add empty string to that the following join with \0 adds an
        # additional zero at the end of the last string!
        bo.append(b'')
        # Concatenate them as null-terminated strings:
        nullTerminatedStrings = b'\0'.join(bo)

        padLength = padLen4(nullTerminatedStrings)
        self._fp.write(nullTerminatedStrings)
        self._fp.write(b'\1\1\1\1'[:padLength])

        # Update the array header:
        self.__s_update_xt_array_header(startPos, rTypeCode)

    @fmap(bool, numpy.bool_)
    def s_atom_to_xt_array_boolean(self, o):
        """
        Render single boolean items into their corresponding array
        counterpart in R.
        Always convert a boolean atomic value into a specialized boolean
        R vector.
        """
        arr = numpy.array([o])
        self.s_xt_array_boolean(arr)

    @fmap(rtypes.XT_ARRAY_BOOL)
    def s_xt_array_boolean(self, o):
        """
        - o: numpy array or subclass (e.g. TaggedArray) with boolean values
        Note: If o is multi-dimensional a tagged array is created. Also if o
              is of type TaggedArray.
        """
        startPos = self._fp.tell()
        rTypeCode = self.__s_write_xt_array_tag_data(o)

        # A boolean vector starts with its number of boolean values in the
        # vector (as int32):
        structCode = '<'+rtypes.structMap[int]
        self._fp.write(struct.pack(structCode, o.size))
        # Then write the boolean values themselves. Note that R expects binary
        # array data in Fortran order, so prepare this accordingly:
        data = o.tostring(order='F')
        self._fp.write(data)
        # Finally pad the binary data to be of a multiple of four in length:
        self._fp.write(padLen4(data) * b'\xff')

        # Update the array header:
        self.__s_update_xt_array_header(startPos, rTypeCode)

    @fmap(int, numpy.int32, long, numpy.int64, numpy.long, float, complex,
          numpy.float64, numpy.complex, numpy.complex64, numpy.complex128)
    def s_atom_to_xt_array_numeric(self, o):
        """
        Render single numeric items into their corresponding array counterpart
        in R
        """
        if isinstance(o, (int, long, numpy.int64, numpy.long)):
            if rtypes.MIN_INT32 <= o <= rtypes.MAX_INT32:
                # even though this type of data is 'long' it still fits into a
                # normal integer. Good!
                o = int(o)
            else:
                raise ValueError('Cannot serialize long integers larger than '
                                 'MAX_INT32 (**31-1)')

        rTypeCode = rtypes.atom2ArrMap[type(o)]
        structCode = '<'+rtypes.structMap[type(o)]
        length = struct.calcsize(structCode)
        if type(o) is complex:
            self._writeDataHeader(rTypeCode, length*2)
            self._fp.write(struct.pack(structCode, o.real))
            self._fp.write(struct.pack(structCode, o.imag))
        else:
            self._writeDataHeader(rTypeCode, length)
            self._fp.write(struct.pack(structCode, o))

    @fmap(rtypes.XT_ARRAY_CPLX, rtypes.XT_ARRAY_DOUBLE, rtypes.XT_ARRAY_INT)
    def s_xt_array_numeric(self, o):
        """
        @param o: numpy array or subclass (e.g. TaggedArray)
        @note: If o is multi-dimensional a tagged array is created. Also if o
               is of type TaggedArray.
        """
        if o.dtype in (numpy.int64, numpy.long):
            if rtypes.MIN_INT32 <= o.min() and o.max() <= rtypes.MAX_INT32:
                # even though this type of array is 'long' its values still
                # fit into a normal int32 array. Good!
                o = o.astype(numpy.int32)
            else:
                raise ValueError('Cannot serialize long integer arrays with '
                                 'values outside MAX_INT32 (2**31-1) range')

        startPos = self._fp.tell()
        rTypeCode = self.__s_write_xt_array_tag_data(o)

        # TODO: make this also work on big endian machines (data must be
        #       written in little-endian!!)

        # Note: R expects binary array data in Fortran order, so prepare this
        # accordingly:
        self._fp.write(o.tostring(order='F'))

        # Update the array header:
        self.__s_update_xt_array_header(startPos, rTypeCode)

    ############### Vectors and Tag lists #####################################

    @fmap(list, TaggedList)
    def s_xt_vector(self, o):
        """Render all objects of given python list into generic r vector"""
        startPos = self._fp.tell()
        # remember start position for calculating length in bytes of entire
        # list content
        attrFlag = rtypes.XT_HAS_ATTR if o.__class__ == TaggedList else 0
        self._writeDataHeader(rtypes.XT_VECTOR | attrFlag, 0)
        if attrFlag:
            self.s_xt_tag_list([(b'names', numpy.array(o.keys))])
        for v in o:
            self.serializeExpr(v)
        length = self._fp.tell() - startPos
        self._fp.seek(startPos)
        # now write header again with correct length information
        # subtract 4 (omit list header!)
        self._writeDataHeader(rtypes.XT_VECTOR | attrFlag, length - 4)
        self._fp.seek(0, os.SEEK_END)

    def s_xt_tag_list(self, o):
        startPos = self._fp.tell()
        self._writeDataHeader(rtypes.XT_LIST_TAG, 0)
        for tag, data in o:
            self.serializeExpr(data)
            self.s_string_or_symbol(tag, rTypeCode=rtypes.XT_SYMNAME)
        length = self._fp.tell() - startPos
        self._fp.seek(startPos)
        # now write header again with correct length information
        # subtract 4 (omit list header!)
        self._writeDataHeader(rtypes.XT_LIST_TAG, length - 4)
        self._fp.seek(0, os.SEEK_END)

    ############################################################
    #### class methods for calling specific Rserv functions ####

    @classmethod
    def rEval(cls, aString, fp=None, void=False):
        """
        Create binary code for evaluating a string expression remotely in
        Rserve
        """
        cmd = rtypes.CMD_voidEval if void else rtypes.CMD_eval
        s = cls(cmd, fp=fp)
        s.serialize(aString, dtTypeCode=rtypes.DT_STRING)
        return s.finalize()

    @classmethod
    def rAssign(cls, varname, o, fp=None):
        """
        Create binary code for assigning an expression to a variable remotely
        in Rserve
        """
        s = cls(rtypes.CMD_setSEXP, fp=fp)
        s.serialize(varname, dtTypeCode=rtypes.DT_STRING)
        s.serialize(o, dtTypeCode=rtypes.DT_SEXP)
        return s.finalize()

    @classmethod
    def rShutdown(cls, fp=None):
        s = cls(rtypes.CMD_shutdown, fp=fp)
        return s.finalize()

    @classmethod
    def rSerializeResponse(cls, Rexp, fp=None):
        # mainly used for unittesting
        s = cls(rtypes.RESP_OK, fp=fp)
        s.serialize(Rexp, dtTypeCode=rtypes.DT_SEXP)
        return s.finalize()


# Some shortcuts:
rEval = RSerializer.rEval
rAssign = RSerializer.rAssign
rSerializeResponse = RSerializer.rSerializeResponse
rShutdown = RSerializer.rShutdown
