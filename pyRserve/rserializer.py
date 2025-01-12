"""
Serializer class to convert Python objects into a binary data stream for
sending them to Rserve.
"""
import os
import io
import struct
import socket

import numpy

from . import rtypes
from .misc import FunctionMapper, byteEncode, padLen4, string2bytesPad4
from .taggedContainers import TaggedList, TaggedArray

# turn on DEBUG to see extra information about what the serializer is
# doing with your data
DEBUG = 0

NoneType = type(None)


class RSerializer:
    """
    Class to serialize Python objects into a binary data stream for sending
    them to Rserve.

    Depending on 'commandType' given to __init__ the resulting binary string
    can be used to send a command, to assign a variable in Rserve, or to
    reply to a request received from Rserve.
    """
    serializeMap = {}
    fmap = FunctionMapper(serializeMap)

    def __init__(self, commandType, fp=None):
        if isinstance(fp, socket.socket):
            self._fp = fp
            self._buffer = io.BytesIO()
        elif not fp:
            self._buffer = fp or io.BytesIO()
            self._fp = None
        else:
            # expect fp to be a seekable file(-like) object:
            self._buffer = self._fp = fp
        self._dataSize = 0
        self._writeHeader(commandType)

    def _getRetVal(self):
        if self._fp is self._buffer:
            # file(-like) object - data has been written, nothing to return
            return None
        elif not self._fp:
            # data has only been written into buffer, so return its value:
            return self._buffer.getvalue()
        else:
            # i.e. socket: write result of _fp into socket-fp
            self._fp.send(self._buffer.getvalue())
            return None

    def _writeHeader(self, commandType):
        """Write main header of message for Rserve"""
        # Set length to zero initially, will be fixed in _finalizerHeader()
        # when msg size is determined:
        msg_length_lower = msg_length_higher = 0
        data_offset = 0
        header = struct.pack('<IIII', commandType, msg_length_lower,
                             data_offset, msg_length_higher)
        if DEBUG:
            print('Writing header: %d bytes: %s' % (len(header), repr(header)))
        self._buffer.write(header)

    def finalize(self):
        """Finalize the message package before actually sending/wriring it out.
        -> Set the length of the entire data package in the general message hdr
           as number of bytes of the entire message minus the general hdr
        """
        # Jump to end of buffer to determine its length:
        self._buffer.seek(0, os.SEEK_END)
        message_size = self._buffer.tell() - rtypes.RHEADER_SIZE
        if DEBUG:
            print('writing size of header: %2d' % message_size)
        # Goto position 4 of the general Rserve package header and write the
        # size of the overall rserve message there. For message size > 2**32
        # the size is split into two parts, the lower 32 bits are written at
        # position 4, the higher part is written at position 12 (see QAP1 docs)
        bin_message_size = struct.pack('<Q', message_size)
        bin_message_size_lo = bin_message_size[:4]
        bin_message_size_hi = bin_message_size[4:]

        self._buffer.seek(4)
        self._buffer.write(bin_message_size_lo)
        self._buffer.write(b'\x00\x00\x00\x00')  # data offset, zero by default
        self._buffer.write(bin_message_size_hi)
        return self._getRetVal()

    def _writeDataHeader(self, rTypeCode, length):
        """Write a header for either DataTypes (DT_*) or ExpressionTypes (XT_*)

        According to the documentation of Rserve:
        -----------------------------------------
        If the length of the data block is smaller than 2**24 - 16 (fffff0)
        then the header has a length of 4 bytes and looks like:
            [1]   rTypeCode
            [2-4] length of data block (3 bytes/24 bits)
        If the length of the data is larger, then the rTypeCode of the header
        has to be OR'ed with XT_LARGE (or DT_LARGE, which is the same). Then
        the length of the datablock can be encoded in 7 bytes:
            [1]   rTypeCode
            [2-4] length of data block (lower three bytes)
            [5-8] length of data block (upper four bytes)

        However; pyRserve is not capable of dynamic header sizes, so we will
                 use the large header setup for all data packages no matter of
                 their size. Simon Urbanek confirmed that this does not cause
                 any problems with Rserve.
        """
        rTypeCode |= rtypes.XT_LARGE
        hdr = struct.pack('<BQ', rTypeCode, length)
        # cut-off leftover zeros at the right end of the header string
        # before writing it to the buffer:
        self._buffer.write(hdr[:rtypes.LARGE_DATA_HEADER_SIZE])
        return rtypes.LARGE_DATA_HEADER_SIZE

    def serialize(self, o, dtTypeCode=rtypes.DT_SEXP):
        # Here the data typecode (DT_* ) of the entire message is written,
        # with its length. Then the actual data itself is written out.
        if dtTypeCode == rtypes.DT_STRING:
            padded_string = string2bytesPad4(o)
            length = len(padded_string)
            hdr_size = self._writeDataHeader(dtTypeCode, length)
            self._buffer.write(padded_string)
        elif dtTypeCode == rtypes.DT_INT:
            length = 4   # an integer is encoded as 4 bytes
            hdr_size = self._writeDataHeader(dtTypeCode, length)
            self._buffer.write(struct.pack('<i', o))
        elif dtTypeCode == rtypes.DT_SEXP:
            start_pos = self._buffer.tell()
            self._buffer.write(b'\0\0\0\0\0\0\0\0')
            length = self.serializeExpr(o)
            self._buffer.seek(start_pos)
            hdr_size = self._writeDataHeader(dtTypeCode, length)
        else:
            raise NotImplementedError('no support for DT-type %x' % dtTypeCode)
        # Jump back to end of buffer to be prepared for writing more data
        self._buffer.seek(0, os.SEEK_END)
        # Adjust datasize counter
        self._dataSize += length + hdr_size

    def serializeExpr(self, o):
        if isinstance(o, numpy.ndarray):
            r_type_code = rtypes.numpyMap[o.dtype.type]
        else:
            r_type_code = type(o)
        try:
            s_func = self.serializeMap[r_type_code]
        except KeyError:
            raise NotImplementedError('Serialization of "%s" not implemented' %
                                      r_type_code)
        start_pos = self._buffer.tell()
        if DEBUG:
            print('Serializing expr %r with r_type_code=%s using function %s' %
                  (o, r_type_code, s_func))
        s_func(self, o)
        # determine and return the length of actual R expression data:
        return self._buffer.tell() - start_pos

    @fmap(NoneType, rtypes.XT_NULL)
    def s_null(self, _):
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
        padded_string = string2bytesPad4(o)
        length = len(padded_string)
        self._writeDataHeader(rTypeCode, length)
        if DEBUG:
            print('Writing string: %2d bytes: %s' %
                  (length, repr(padded_string)))
        self._buffer.write(padded_string)

    # ############### Arrays #########################################

    def __s_write_xt_array_tag_data(self, o):
        """
        Write tag data of an array, like dimension for a multi-dim array,
        or other information found. Return appropriate r_type_code.
        """
        xt_tag_list = []
        if o.ndim > 1:
            xt_tag_list.append((b'dim', numpy.array(o.shape, numpy.int32)))
        if isinstance(o, TaggedArray):
            xt_tag_list.append((b'names', numpy.array(o.attr)))

        attr_flag = rtypes.XT_HAS_ATTR if xt_tag_list else 0
        r_type_code = rtypes.numpyMap[o.dtype.type] | attr_flag
        # write length of zero for now, will be corrected later:
        self._writeDataHeader(r_type_code, 0)
        if attr_flag:
            self.s_xt_tag_list(xt_tag_list)
        return r_type_code

    def __s_update_xt_array_header(self, headerPos, rTypeCode):
        """
        Update length information of xt array header which has been
        previously temporarily set to 0 in __s_write_xt_array_tag_data()
        @arg headerPos: file position where header information should be
                        written.
        @arg rTypeCode
        """
        # subtract length of data header (8 bytes), does not count to payload!
        length = self._buffer.tell() - headerPos - rtypes.LARGE_DATA_HEADER_SIZE
        self._buffer.seek(headerPos)
        self._writeDataHeader(rTypeCode, length)
        self._buffer.seek(0, os.SEEK_END)

    @fmap(*rtypes.STRING_TYPES)
    def s_xt_array_single_str(self, o):
        """Serialize single string object"""
        arr = numpy.array([o])
        self.s_xt_array_str(arr)

    @fmap(rtypes.XT_ARRAY_STR)
    def s_xt_array_str(self, o):
        """Serialize array of strings"""
        start_pos = self._buffer.tell()
        r_type_code = self.__s_write_xt_array_tag_data(o)

        # reshape into 1d array:
        o1d = o.reshape(o.size, order='F')
        # Byte-encode them:
        bo = [byteEncode(d) for d in o1d]
        # add empty string so that the following join with \0 adds an
        # extra zero at the end of the last string!
        bo.append(b'')
        # Concatenate them as null-terminated strings:
        null_terminated_strings = b'\0'.join(bo)

        pad_length = padLen4(null_terminated_strings)
        self._buffer.write(null_terminated_strings)
        self._buffer.write(b'\1\1\1\1'[:pad_length])

        # Update the array header:
        self.__s_update_xt_array_header(start_pos, r_type_code)

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
        start_pos = self._buffer.tell()
        r_type_code = self.__s_write_xt_array_tag_data(o)

        # A boolean vector starts with its number of boolean values in the
        # vector (as int32):
        struct_code = '<'+rtypes.structMap[int]
        self._buffer.write(struct.pack(struct_code, o.size))
        # Then write the boolean values themselves. Note that R expects binary
        # array data in Fortran order, so prepare this accordingly:
        data = o.tobytes(order='F')
        self._buffer.write(data)
        # Finally pad the binary data to be of a multiple of four in length:
        self._buffer.write(padLen4(data) * b'\xff')

        # Update the array header:
        self.__s_update_xt_array_header(start_pos, r_type_code)

    @fmap(int, numpy.int32, numpy.int64, numpy.long, float, complex,
          numpy.float64, numpy.complex64, numpy.complex128)
    def s_atom_to_xt_array_numeric(self, o):
        """
        Render single numeric items into their corresponding array counterpart
        in R
        """
        if isinstance(o, (int, numpy.int64, numpy.long)):
            if rtypes.MIN_INT32 <= o <= rtypes.MAX_INT32:
                o = int(o)
            else:
                raise ValueError('Cannot serialize long integers larger than '
                                 'MAX_INT32 (**31-1)')

        r_type_code = rtypes.atom2ArrMap[type(o)]
        struct_code = '<'+rtypes.structMap[type(o)]
        length = struct.calcsize(struct_code)
        if type(o) is complex:
            self._writeDataHeader(r_type_code, length*2)
            self._buffer.write(struct.pack(struct_code, o.real))
            self._buffer.write(struct.pack(struct_code, o.imag))
        else:
            self._writeDataHeader(r_type_code, length)
            self._buffer.write(struct.pack(struct_code, o))

    @fmap(rtypes.XT_ARRAY_CPLX, rtypes.XT_ARRAY_DOUBLE, rtypes.XT_ARRAY_INT)
    def s_xt_array_numeric(self, o):
        """
        @param o: numpy array or subclass (e.g. TaggedArray)
        @note: If o is multidimensional a tagged array is created. Also if o
               is of type TaggedArray.
        """
        if o.dtype in (numpy.int64, numpy.long):
            # Note: use int instead of compat.long once Py2 is abandoned.
            if rtypes.MIN_INT32 <= o.min() and o.max() <= rtypes.MAX_INT32:
                # even though this type of array is 'long' its values still
                # fit into a normal int32 array. Good!
                o = o.astype(numpy.int32)
            else:
                raise ValueError('Cannot serialize long integer arrays with '
                                 'values outside MAX_INT32 (2**31-1) range')

        start_pos = self._buffer.tell()
        r_type_code = self.__s_write_xt_array_tag_data(o)

        # TODO: make this also work on big endian machines (data must be
        #       written in little-endian!!)

        # Note: R expects binary array data in Fortran order, so prepare this
        # accordingly:
        self._buffer.write(o.tobytes(order='F'))

        # Update the array header:
        self.__s_update_xt_array_header(start_pos, r_type_code)

    # ############## Vectors and Tag lists ####################################

    @fmap(list, TaggedList)
    def s_xt_vector(self, o):
        """Render all objects of given python list into generic r vector"""
        start_pos = self._buffer.tell()
        # remember start position for calculating length in bytes of entire
        # list content
        attr_flag = rtypes.XT_HAS_ATTR if o.__class__ == TaggedList else 0
        self._writeDataHeader(rtypes.XT_VECTOR | attr_flag, 0)
        if attr_flag:
            self.s_xt_tag_list([(b'names', numpy.array(o.keys))])
        for v in o:
            self.serializeExpr(v)
        length = self._buffer.tell() - start_pos
        self._buffer.seek(start_pos)
        # now write header again with correct length information
        # subtract length of list data header:
        self._writeDataHeader(rtypes.XT_VECTOR | attr_flag,
                              length - rtypes.LARGE_DATA_HEADER_SIZE)
        self._buffer.seek(0, os.SEEK_END)

    def s_xt_tag_list(self, o):
        start_pos = self._buffer.tell()
        self._writeDataHeader(rtypes.XT_LIST_TAG, 0)
        for tag, data in o:
            self.serializeExpr(data)
            self.s_string_or_symbol(tag, rTypeCode=rtypes.XT_SYMNAME)
        length = self._buffer.tell() - start_pos
        self._buffer.seek(start_pos)
        # now write header again with correct length information
        # subtract length of list data header:
        self._writeDataHeader(rtypes.XT_LIST_TAG,
                              length - rtypes.LARGE_DATA_HEADER_SIZE)
        self._buffer.seek(0, os.SEEK_END)

    # ##########################################################
    # ### class methods for calling specific Rserv functions ###

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
