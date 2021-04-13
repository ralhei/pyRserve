"""
types module for pyRserve
"""
import numpy
from pyRserve.misc import PY3

# some general constants:
SOCKET_BLOCK_SIZE = 4096
MAX_INT32 = 2**31 - 1
MIN_INT32 = -MAX_INT32

# Rserve constants and mappings ###############################################

# Main Rserve header size [bytes]
RHEADER_SIZE = 16

# Header sizes (in SEXPR) without and with XT_LARGE or DT_LARGE flag [bytes]
SMALL_DATA_HEADER_SIZE = 4
LARGE_DATA_HEADER_SIZE = 8


CMD_RESP = 0x10000            # all responses have this flag set

RESP_OK  = CMD_RESP | 0x0001  # command succeeded; returned parameters depend
                              # on the command issued
RESP_ERR = CMD_RESP | 0x0002  # command failed, check stats code


CMD_OOB         = 0x20000     # out-of-band data - i.e. unsolicited messages

OOB_SEND        = CMD_OOB | 0x1000  # OOB send - unsolicited SEXP sent from the
                                    # R instance to the client. 12 LSB are
                                    # reserved for application-specific code
OOB_MSG         = CMD_OOB | 0x2000  # OOB message - unsolicited message sent
                                    # from the R instance to the client
                                    # requiring a response. 12 LSB are reserved
                                    # for application-specific code
OOB_STREAM_READ = CMD_OOB | 0x4000  # OOB stream read request - server requests
                                    # streaming data from the client (typically
                                    # streaming input for computation)

###############################################################################
# Error codes

ERR_auth_failed      = 0x41  # auth.failed or auth.requested but no
                             #   login came. in case of authentification
                             #   failure due to name/pwd mismatch,
                             #   server may send CMD_accessDenied instead

ERR_conn_broken      = 0x42  # connection closed or broken packet killed it
ERR_inv_cmd          = 0x43  # unsupported/invalid command
ERR_inv_par          = 0x44  # some parameters are invalid
ERR_Rerror           = 0x45  # R-error occured, usually followed by connection
                             #   shutdown
ERR_IOerror          = 0x46  # I/O error
ERR_notOpen          = 0x47  # attempt to perform fileRead/Write on closed file
ERR_accessDenied     = 0x48  # this answer is also valid on
                             #   CMD_login; otherwise it's sent
                             #   if the server deosn;t allow the user
                             #   to issue the specified command.
                             #   (e.g. some server admins may block
ERR_unsupportedCmd   = 0x49  # unsupported command
ERR_unknownCmd       = 0x4a  # unknown command - the difference
                             #   between unsupported and unknown is that
                             #   unsupported commands are known to the
                             #   server but for some reasons (e.g.
                             #   platform dependent) it's not supported.
                             #   unknown commands are simply not recognized
                             #   by the server at all.

# The following ERR_.. exist since 1.23/0.1-6
ERR_data_overflow    = 0x4b  # incoming packet is too big.
                             #   currently there is a limit as of the
                             #   size of an incoming packet.
ERR_object_too_big   = 0x4c  # the requested object is too big
                             #   to be transported in that way.
                             #   If received after CMD_eval then
                             #   the evaluation itself was successful.
                             #   optional parameter is the size of the object

# since 1.29/0.1-9
ERR_out_of_mem       = 0x4d  # out of memory. the connection is usually
                             #  closed after this error was sent
# since 0.6-0
ERR_ctrl_closed      = 0x4e  # control pipe to the master process is closed
                             #  or broken

# since 0.4-0
ERR_session_busy     = 0x50  # session is still busy
ERR_detach_failed    = 0x51  # unable to detach seesion (cannot determine
                             #  peer IP or problems creating a listening socket
                             #  for resume)

# pack all error codes with their names into a dictionary:
ERRORS = dict([(errCode, err_name) for (err_name, errCode) in locals().items()
               if err_name.startswith('ERR_')])


###############################################################################
# Available commands

CMD_login        = 0x001    # "name\npwd" : -
CMD_voidEval     = 0x002    # string : -
CMD_eval         = 0x003    # string : encoded SEXP
CMD_shutdown     = 0x004    # [admin-pwd] : -

# file I/O routines. server may answe
CMD_openFile     = 0x010    # fn : -
CMD_createFile   = 0x011    # fn : -
CMD_closeFile    = 0x012    # - : -
CMD_readFile     = 0x013    # [int size] : data... ; if size not present,
                            #      server is free to choose any value - usually
                            #      it uses the size of its static buffer
CMD_writeFile    = 0x014    # data : -
CMD_removeFile   = 0x015    # fn : -

# object manipulation
CMD_setSEXP      = 0x020    # string(name), REXP : -
CMD_assignSEXP   = 0x021    # string(name), REXP : - ; same as setSEXP
                            #    except that the name is parsed

# session management (since 0.4-0)
CMD_detachSession    = 0x030  # : session key
CMD_detachedVoidEval = 0x031  # string : session key; doesn't
CMD_attachSession    = 0x032  # session key : -

# control commands (since 0.6-0) - passed on to the master process
# Note: currently all control commands are asychronous, i.e. RESP_OK
#   indicates that the command was enqueued in the master pipe, but there
#  is no guarantee that it will be processed. Moreover non-forked
#   connections (e.g. the default debug setup) don't process any
#   control commands until the current client connection is closed so
#   the connection issuing the control command will never see its result.

CMD_ctrl            = 0x40  # -- not a command - just a constant --
CMD_ctrlEval        = 0x42  # string : -
CMD_ctrlSource      = 0x45  # string : -
CMD_ctrlShutdown    = 0x44  # - : -

# 'internal' commands (since 0.1-9)
CMD_setBufferSize   = 0x081   # [int sendBufSize]
                              #     this commad allow clients to request
                              #     bigger buffer sizes if large data is to be
                              #     transported from Rserve to the client.
                              #     (incoming buffer is resized automatically)

CMD_setEncoding     = 0x082   # string (one of "native","latin1","utf8")

# special commands - the payload of packages with this mask does not contain
# defined parameters

CMD_SPECIAL_MASK    = 0xf0

CMD_serEval         = 0xf5     # serialized eval - the packets are raw
                               #   serialized data without data header
CMD_serAssign       = 0xf6     # serialized assign - serialized list with
                               #   [[1]]=name, [[2]]=value
CMD_serEEval        = 0xf7     # serialized expression eval - like serEval with
                               #   one additional evaluation round


###############################################################################
# Data types for the transport protocol (QAP1) do NOT confuse with any
# XT_.. values.

DT_INT           = 0x01  # int
DT_CHAR          = 0x02  # char
DT_DOUBLE        = 0x03  # double
DT_STRING        = 0x04  # 0 terminted string
DT_BYTESTREAM    = 0x05  # stream of bytes (unlike DT_STRING may contain 0)
DT_SEXP          = 0x0A  # encoded SEXP

DT_ARRAY         = 0x0B  # array of objects (i.e. first 4 bytes specify how
                         #   many subsequent objects are part of the array;
                         #   0 is legitimate)
DT_LARGE         = 0x40  # new in 0102: if this flag is set then the length of
                         #   the object is coded as 56-bit integer enlarging
                         # the header by 4 bytes

###############################################################################
# XpressionTypes

#   REXP - R expressions are packed in the same way as command parameters
#   transport format of the encoded Xpressions:
#   [0] int type/len (1 byte type, 3 bytes len - same as SET_PAR)
#   [4] REXP attr (if bit 8 in type is set)
#   [4/8] data ..

XT_NULL          =  0x00  # P  data: [0]
XT_INT           =  0x01  # -  data: [4]int
XT_DOUBLE        =  0x02  # -  data: [8]double
XT_STR           =  0x03  # P  data: [n]char null-term. strg.
XT_LANG          =  0x04  # -  data: same as XT_LIST
XT_SYM           =  0x05  # -  data: [n]char symbol name
XT_BOOL          =  0x06  # -  data: [1]byte boolean (1=TRUE, 0=FALSE, 2=NA)

XT_S4            =  0x07  # P  data: [0]

XT_BYTE          =  0x08  # extension for pyRserve
XT_INT3          =  0x09  # extension for pyRserve, a 3-byte integer as used
                          #   in REXP
XT_INT7          =  0x0A  # extension for pyRserve, a 7-byte integer as used
                          #   in REXP

XT_VECTOR        =  0x10  # 16dec: P  data: [?]REXP,REXP,..
XT_LIST          =  0x11  # 17dec: -  X head, X vals, X tag (since 0.1-5)
XT_CLOS          =  0x12  # 18dec: P  X formals, X body  (closure; since 0.1-5)
XT_SYMNAME       =  0x13  # 19dec: s  same as XT_STR (since 0.5)
XT_LIST_NOTAG    =  0x14  # 20dec: s  same as XT_VECTOR (since 0.5)
XT_LIST_TAG      =  0x15  # 21dec: P  X tag, X val, Y tag, Y val,  (since 0.5)
XT_LANG_NOTAG    =  0x16  # 22dec: s  same as XT_LIST_NOTAG (since 0.5)
XT_LANG_TAG      =  0x17  # 23dec: s  same as XT_LIST_TAG (since 0.5)
XT_VECTOR_EXP    =  0x1a  # 26dec: s  same as XT_VECTOR (since 0.5)
XT_VECTOR_STR    =  0x1b  # 27dec: -  same as XT_VECTOR (since 0.5 but unused,
                          #           use XT_ARRAY_STR instead)

XT_ARRAY_INT     =  0x20  # 32dec: P  data: [n*4]int,int,..
XT_ARRAY_DOUBLE  =  0x21  # 33dec: P  data: [n*8]double,double,..
XT_ARRAY_STR     =  0x22  # 34dec: P  data: string,string,.. (
                          #           string=byte,byte,...,0) padded with '\01'
XT_ARRAY_BOOL_UA =  0x23  # 35dec: -  data: [n]byte,byte,..
                          #           (unaligned! NOT supported anymore)
XT_ARRAY_BOOL    =  0x24  # 36dec: P  data: int(n),byte,byte,...
XT_RAW           =  0x25  # 37dec: P  data: int(n),byte,byte,...
XT_ARRAY_CPLX    =  0x26  # 38dec: P  data: [n*16]double,double,...
                          #           (Re,Im,Re,Im,...)

XT_UNKNOWN       =  0x30  # 48dec: P  data: [4]int - SEXP
#                                     type (as from TYPEOF(x))
#                      |
#                      +--- interesting flags for client implementations:
#                           P = primary type
#                           s = secondary type - its decoding is identical to
#                               a primary type and thus the client doesn't need
#                                to decode it separately.
#                           - = deprecated/removed. if a client doesn't need to
#                               support old Rserve versions, those can be
#                               safely skipped.
#  Total primary: 4 trivial types (NULL, STR, S4, UNKNOWN) + 6 array types +
#                 3 recursive types


XT_LARGE         =  0x40  # 64dec: new in 0102: if this flag is set then the
                          #   length of the object is coded as 56-bit integer
                          #   enlarging the header by 4 bytes
XT_HAS_ATTR      =  0x80  # 128dec: flag; if set, the following REXP is the
                          #   attribute the use of attributes and vectors
                          #   results in recursive storage of REXPs

# Build up a dictionary that translates all codes for XT_* and DT_* constants
# into their names:

XTs = dict([(rTypeCode, xt_name) for (xt_name, rTypeCode) in locals().items()
            if xt_name.startswith('XT_')])
DTs = dict([(rTypeCode, dt_name) for (dt_name, rTypeCode) in locals().items()
            if dt_name.startswith('DT_')])


BOOL_TRUE = 1
BOOL_FALSE = 0
BOOL_NA = 2

VALID_R_TYPES = [
    DT_SEXP, XT_BOOL, XT_INT, XT_DOUBLE, XT_STR, XT_SYMNAME, XT_VECTOR,
    XT_LIST_TAG, XT_LANG_TAG, XT_LIST_NOTAG, XT_LANG_NOTAG, XT_CLOS,
    XT_ARRAY_BOOL, XT_ARRAY_INT, XT_ARRAY_DOUBLE, XT_ARRAY_CPLX, XT_ARRAY_STR,
    XT_VECTOR_EXP, XT_NULL, XT_UNKNOWN, XT_RAW, XT_S4
]

STRING_TYPES = [str, numpy.string_, numpy.str_]
if not PY3:
    STRING_TYPES.append(unicode)  # noqa: F821      'unicode' unknown in Python3

###############################################################################
# Mapping btw. numpy and R data types, in both directions

# map r-types and some python types to typecodes used in the 'struct' module
structMap = {
    XT_BOOL:          'b',
    bool:             'b',
    XT_BYTE:          'B',
    XT_INT:           'i',
    int:              'i',
    numpy.int32:      'i',
    XT_INT3:          'i',
    XT_INT7:          'q',     # 64 bit integer
    XT_DOUBLE:        'd',     # double (float64)
    float:            'd',
    numpy.double:     'd',
    complex:          'd',
    complex:          'd',
    numpy.complex128: 'd',
}

# mapping to determine overall type of message.
DT_Map = {
    str:    DT_STRING,
    int:    DT_INT,
    float:  DT_DOUBLE,
}


numpyMap = {
    XT_ARRAY_BOOL:     numpy.bool_,
    XT_ARRAY_INT:      numpy.int32,
    XT_ARRAY_DOUBLE:   numpy.double,     # double float64
    XT_ARRAY_CPLX:     complex,
    XT_ARRAY_STR:      numpy.string_,
}

# also add the inverse mapping to it:
for k, v in list(numpyMap.items()):
    numpyMap[v] = k

# some manual additions for numpy variants:
numpyMap[numpy.complex128]  = XT_ARRAY_CPLX
numpyMap[numpy.int32]       = XT_ARRAY_INT
numpyMap[numpy.int64]       = XT_ARRAY_INT
numpyMap[numpy.compat.long] = XT_ARRAY_INT
numpyMap[numpy.str_]        = XT_ARRAY_STR
numpyMap[numpy.unicode_]    = XT_ARRAY_STR


atom2ArrMap = {
    # map atomic python objects to their array counterparts in R
    int:               XT_ARRAY_INT,
    numpy.int32:       XT_ARRAY_INT,
    float:             XT_ARRAY_DOUBLE,
    numpy.double:      XT_ARRAY_DOUBLE,
    complex:           XT_ARRAY_CPLX,
    numpy.complex128:  XT_ARRAY_CPLX,
    str:               XT_ARRAY_STR,
    numpy.str_:        XT_ARRAY_STR,
    numpy.string_:     XT_ARRAY_STR,
    numpy.unicode_:    XT_ARRAY_STR,
    bool:              XT_ARRAY_BOOL,
}
