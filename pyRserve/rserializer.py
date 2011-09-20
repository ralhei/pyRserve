"""
Serializer class to convert Python objects into a binary data stream for sending them to Rserve.
"""

__all__ = ['reval', 'rassign', 'rSerializeResponse']

import struct, os, cStringIO, socket
###
import numpy
###
import rtypes
from misc import FunctionMapper
from rexceptions import RSerializationError
from taggedContainers import TaggedList, TaggedArray

# turn on DEBUG to see extra information about what the serializer is doing with your data
DEBUG = False


def padLen4(aString):
    """Calculate how many additional bytes a given string needs to have a length of a multiple of 4"""
    l = len(aString)
    return 4-divmod(l, 4)[1]


def padString4(aString, padByte='\0'):
    """return a given string padded with zeros at the end to make its length be a multiple of 4"""
    return aString + padLen4(aString) * padByte



class RSerializer(object):
    """
    Class to to serialize Python objects into a binary data stream for sending them to Rserve.

    Depending on 'commandType' given to __init__ the resulting binary string can be used to send a command, to assign
    a variable in Rserve, or to reply to a request received from Rserve.
    """
    serializeMap = {}
    fmap = FunctionMapper(serializeMap)
    #
    def __init__(self, commandType, fp=None):
        if isinstance(fp, socket._socketobject):
            self._orig_fp = fp.makefile()
            self._fp = cStringIO.StringIO()
        elif not fp:
            self._fp = fp or cStringIO.StringIO()
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
            self._orig_fp.write(self._fp.getvalue())
            self._orig_fp.flush()
            return None

    def _writeHeader(self, commandType):
        # Set length to zero initially, will be fixed in _finalizerHeader() when msg size is determined:
        msg_length_lower = msg_length_higher = 0
        data_offset = 0
        header = struct.pack('<IIII', commandType, msg_length_lower, data_offset, msg_length_higher)
        if DEBUG:
            print 'Writing header: %d bytes: %s' % (len(header), repr(header))
        self._fp.write(header)

    def finalize(self):
        # and finally we correctly set the length of the entire data package (in bytes) minus header size:
        # dataSize = self._fp.tell() - rtypes.RHEADER_SIZE
        # TODO: Also handle data larger than 2**32 (user upper part of message length!!)
        assert self._dataSize < 2**32, 'data larger than 2**32 not yet implemented'
        self._fp.seek(4)
        if DEBUG:
            print 'writing size of header: %2d' % self._dataSize
        self._fp.write(struct.pack('<I', self._dataSize))
        return self._getRetVal()
        
    def _writeDataHeader(self, rTypeCode, length):
        '''
        A data header consists of 4 bytes:
        [1]   rTypeCode
        [2-4] length of data block (3 bytes!!!)
        '''
        self._fp.write(struct.pack('<Bi', rTypeCode, length)[:4])
        
    def serialize(self, o, dtTypeCode=rtypes.DT_SEXP):
        # Here the data typecode (DT_* ) of the entire message is written, with its length. 
        # Then the actual data itself is written out.
        if dtTypeCode == rtypes.DT_STRING:
            paddedString = padString4(o)
            length = len(paddedString)
            self._writeDataHeader(dtTypeCode, length)
            self._fp.write(paddedString)
        elif dtTypeCode == rtypes.DT_INT:
            length = 4
            self._writeDataHeader(dtTypeCode, length)
            self._fp.write(struct.pack('<i', o))
        elif dtTypeCode == rtypes.DT_SEXP:
            startPos = self._fp.tell()
            self._fp.write('\0\0\0\0')
            length = self._serializeExpr(o)
            self._fp.seek(startPos)
            self._writeDataHeader(dtTypeCode, length)
        else:
            raise NotImplementedError('no support for DT-type %x' % dtTypeCode)
        self._dataSize += length + 4

    def _serializeExpr(self, o, rTypeHint=None):
        if not rTypeHint:
            if isinstance(o, numpy.ndarray):
                rTypeHint = rtypes.numpyMap[o.dtype.type]   #o.dtype.type
            else:
                rTypeHint = type(o)
        try:
            s_func = self.serializeMap[rTypeHint]
        except KeyError:
            raise RSerializationError('Serialization of type "%s" not implemented' % rTypeHint)
        startPos = self._fp.tell()
        if DEBUG:
            print 'Serializing expr %r with rTypeCode=%s using function %s' % (o, rTypeHint, s_func)
        s_func(self, o, rTypeCode=rTypeHint)
        # determine and return the length of actual R expression data:
        return self._fp.tell() - startPos
        
    @fmap(rtypes.XT_STR, rtypes.XT_SYMNAME)
    def s_string_or_symbol(self, o, rTypeCode=rtypes.XT_STR):
        '''
        Possible rTypeCodes for a given string are:
        - XT_STR
        - XT_SYMNAME
        '''
        # The string packet contains trailing padding zeros to make it always a multiple of 4 in length:
        paddedString = padString4(o)
        length = len(paddedString)
        self._writeDataHeader(rTypeCode, length)
        if DEBUG:
            print 'Writing string: %2d bytes: %s' % (length, repr(paddedString))
        self._fp.write(paddedString)

    @fmap(str, numpy.string_, rtypes.XT_ARRAY_STR)
    def s_xt_array_str(self, o, rTypeCode=None):
        # Works for single strings, lists of strings, and numpy arrays of strings (dtype 'S' or 'O')
        if type(o) in [str, numpy.string_]:
            # single string
            o = [o]
        zeroSeparatedString = '\0'.join(o)
        padLength = padLen4(zeroSeparatedString)
        length = len(zeroSeparatedString) + padLength
        self._writeDataHeader(rtypes.XT_ARRAY_STR, length)
        self._fp.write(zeroSeparatedString)
        self._fp.write('\0\1\1\1'[:padLength])
    

    def __s_xt_array_numeric_tag_data(self, o):
        # Determine which tags the array must be given:
        xt_tag_list = []
        if o.ndim > 1:
            xt_tag_list.append(('dim', numpy.array(o.shape, numpy.int32)))
        if isinstance(o, TaggedArray):
            xt_tag_list.append(('names', numpy.array(o.attr)))

        attrFlag = rtypes.XT_HAS_ATTR if xt_tag_list else 0
        rTypeCode = rtypes.numpyMap[o.dtype.type] | attrFlag
        self._writeDataHeader(rTypeCode, 0)
        if attrFlag:
            self.s_xt_tag_list(xt_tag_list)
        return rTypeCode

    @fmap(rtypes.XT_ARRAY_CPLX, rtypes.XT_ARRAY_DOUBLE, rtypes.XT_ARRAY_INT)
    def s_xt_array_numeric(self, o, rTypeCode=None):
        '''
        @param o: numpy array or subclass (e.g. TaggedArray)
        @note: If o is multi-dimensional a tagged array is created. Also if o is of type TaggedArray.
        '''
        startPos = self._fp.tell()
        rTypeCode = self.__s_xt_array_numeric_tag_data(o)

        # TODO: make this also work on big endian machines (data must be written in little-endian!!)
        self._fp.write(o.tostring())
        length = self._fp.tell() - startPos - 4  # subtract length of header==4 bytes
        self._fp.seek(startPos)
        self._writeDataHeader(rTypeCode, length)
        self._fp.seek(0, os.SEEK_END)
        
    @fmap(rtypes.XT_ARRAY_BOOL)
    def s_xt_array_boolean(self, o, rTypeCode=None):
        '''
        @param o: numpy array or subclass (e.g. TaggedArray) with boolean values
        @note: If o is multi-dimensional a tagged array is created. Also if o is of type TaggedArray.
        '''
        startPos = self._fp.tell()
        rTypeCode = self.__s_xt_array_numeric_tag_data(o)

        # A boolean vector starts with its number of boolean values in the vector (as int32):
        structCode = '<'+rtypes.structMap[int]
        self._fp.write(struct.pack(structCode, len(o)))
        # Then write the boolean values themselves:
        data = o.tostring()
        self._fp.write(data)
        # Finally pad the binary data to be of a multiple of four in length:
        self._fp.write(padLen4(data) * "\xff")
        
        # Update the vector header:
        length = self._fp.tell() - startPos - 4  # subtract length of header==4 bytes
        self._fp.seek(startPos)
        self._writeDataHeader(rTypeCode, length)
        self._fp.seek(0, os.SEEK_END)

    @fmap(int, float, numpy.float64, numpy.int32)
    def s_atom_to_xt_array_numeric(self, o, rTypeCode=None):
        'Render single numeric items into their corresponding array counterpart in r'
        rTypeCode  = rtypes.atom2ArrMap[type(o)]
        structCode = '<'+rtypes.structMap[type(o)]
        length = struct.calcsize(structCode)
        self._writeDataHeader(rTypeCode, length)
        self._fp.write(struct.pack(structCode, o))

    @fmap(bool, numpy.bool_)
    def s_atom_to_xt_array_boolean(self, o, rTypeCode=None):
        """Render single boolean items into their corresponding array counterpart in r.

        Always convert a boolean atomic value into a specialized boolean R vector.
        """
        arr = numpy.array([o])
        self.s_xt_array_boolean(arr)

    @fmap(list, TaggedList)
    def s_xt_vector(self, o, rTypeCode=None):
        'Render all objects of given python list into generic r vector'
        startPos = self._fp.tell()
        # remember start position for calculating length in bytes of entire list content
        attrFlag = rtypes.XT_HAS_ATTR if o.__class__ == TaggedList else 0
        self._writeDataHeader(rtypes.XT_VECTOR | attrFlag, 0)
        if attrFlag:
            self.s_xt_tag_list([('names', numpy.array(o.keys))])
        for v in o:
            self._serializeExpr(v)
        length = self._fp.tell() - startPos
        self._fp.seek(startPos)
        # now write header again with correct length information
        self._writeDataHeader(rtypes.XT_VECTOR | attrFlag, length - 4)  # subtract 4 (omit list header!)
        self._fp.seek(0, os.SEEK_END)
        
    def s_xt_tag_list(self, o, rTypeCode=None):
        startPos = self._fp.tell()
        self._writeDataHeader(rtypes.XT_LIST_TAG, 0)
        for tag, data in o:
            self._serializeExpr(data)
            self._serializeExpr(tag, rTypeHint=rtypes.XT_SYMNAME)
        length = self._fp.tell() - startPos
        self._fp.seek(startPos)
        # now write header again with correct length information
        self._writeDataHeader(rtypes.XT_LIST_TAG, length - 4)  # subtract 4 (omit list header!)
        self._fp.seek(0, os.SEEK_END)
        
        
        

    ############################################################
    #### class methods for calling specific Rserv functions #### 

    @classmethod
    def rEval(cls, aString, fp=None):
        """Create binary code for evaluating a string expression remotely in Rserve"""
        s = cls(rtypes.CMD_eval, fp=fp)
        s.serialize(aString, dtTypeCode=rtypes.DT_STRING)
        return s.finalize()
    
    
    @classmethod
    def rAssign(cls, varname, o, fp=None):
        """Create binary code for assigning an expression to a variable remotely in Rserve"""
        s = cls(rtypes.CMD_setSEXP, fp=fp)
        s.serialize(varname, dtTypeCode=rtypes.DT_STRING)
        s.serialize(o, dtTypeCode=rtypes.DT_SEXP)
        return s.finalize()
    
    
    @classmethod
    def rSerializeResponse(cls, Rexp, fp=None):
        # mainly used for unittesting
        s = cls(rtypes.CMD_RESP | rtypes.RESP_OK, fp=fp)
        s.serialize(Rexp, dtTypeCode=rtypes.DT_SEXP)
        return s.finalize()


# Some shortcuts:
rEval = RSerializer.rEval
rAssign = RSerializer.rAssign
rSerializeResponse = RSerializer.rSerializeResponse
