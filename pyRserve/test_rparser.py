import struct, datetime, socket, threading, py
from numpy import array, ndarray
from numpy.core.records import recarray, record
###
import rtypes, rparser, rserializer
from rexceptions import RSerializationError
from misc import phex
from taggedContainers import TaggedList, asTaggedArray

# rparser.DEBUG = rserializer.DEBUG = True

DEBUG = 0

def shaped_array(data, dtype, shape):
    arr = array(data, dtype=dtype)
    arr.shape = shape
    return arr


r2pyExpressions = [
    ('"abc"',                                   'abc'),
    # a single number is handled R-internal as a vector, but for convience reasons is tranlated 
    # into a single number in Python:
    ('1',                                       1.0),
    # The same for an integer:
    ('as.integer(c(1))',                        1),
    # and again for a explicitely created R vector:
    ('c(1)',                                    1.0),
    ('c(1, 2)',                                 array([1.0, 2.0])),
    ('as.integer(c(1, 2))',                     array([1, 2], dtype=int)),
    ('c("abc", "defghi")',                      array(["abc", "defghi"])),
    ('seq(1, 5)',                               array(range(1, 6), dtype=int)),
    # An explicit R list with only one item remains a list on the python side:
    ('list("otto")',                            ["otto"]),
    ('list("otto", "gustav")',                  ["otto", "gustav"]),
    # tagged lists:
    ('list(husband="otto")',                    TaggedList([("husband", "otto")])),
    ('list(husband="otto", wife="erna")',       TaggedList([("husband", "otto"), ("wife", "erna")])),
    ('list(n="Fred", no_c=2, c_ages=c(4,7))',   TaggedList([("n","Fred"),("no_c",2.),("c_ages",array([4.,7.]))])),
    # tagged array:
    ('c(a=1.,b=2.,c=3.)',                       asTaggedArray(array([1.,2.,3.]),['a','b','c'])),
    # tagged single item array should remain an array on the python side in order to preserve the tag:
    ('c(a=1)',                                  asTaggedArray(array([1.]), ['a'])),
    # multi-dim array (internally also a tagged array) gets translated into a shaped numpy array:
    ('array(1:20, dim=c(4, 5))',                shaped_array(range(1,21), int, (4, 5))),
    #
    #('x<-1:20; y<-x*2; lm(y~x)',                ????),
    # Environment
    #('parent.env',                              [1,2]),
    ]


###############################################3

def test_rExprGenerator():
    '''
    @Brief Main test function generator called from py.test. It generates different test arguments which
           are then fed into the actual testing function "rExprTester()" below.
    '''
    for rExpr, pyExpr in r2pyExpressions:
        if not rExpr in binaryRExpressions.binaryRExpressions:
            # seems like the r2pyExpressions above has changed, but the binaryRExpressions was not rebuilt.
            # Do this now and reload the module:
            createBinaryRExpressions()
            reload(binaryRExpressions)
        yield rExprTester, rExpr, pyExpr, binaryRExpressions.binaryRExpressions[rExpr]


def test_rAssign_method():
    'test "rAssign" class method of RSerializer'
    hexd = '\x20\x00\x00\x00\x14\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x04\x00\x00\x76\x00'\
           '\x00\x00\x0a\x08\x00\x00\x20\x04\x00\x00\x01\x00\x00\x00'
    assert rserializer.rAssign('v', 1) == hexd
    

def test_rEval_method():
    hexd = '\x03\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x04\x00\x00\x61\x3d\x31\x00'
    assert rserializer.rEval('a=1') == hexd


def test_serialize_DT_INT():
    hexd = '\x03\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x04\x00\x007\x00\x00\x00'
    s = rserializer.RSerializer(rtypes.CMD_eval)
    s.serialize(55, dtTypeCode=rtypes.DT_INT)
    res = s.finalize()
    assert hexd == res


def test_serialize_unsupported_object_raises_exception():
    # datetime objects are not yet supported, so an exception can be expected
    py.test.raises(RSerializationError, rserializer.rSerializeResponse, datetime.date.today())


def test_serialize_into_socket():
    rs = PseudoRServer()
    rs.start()
    # now connect to it:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("localhost", PseudoRServer.PORT))
    hexd = '\x03\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x04\x00\x007\x00\x00\x00'
    s = rserializer.RSerializer(rtypes.CMD_eval, fp=sock)
    s.serialize(55, dtTypeCode=rtypes.DT_INT)
    s.finalize()
    assert sock.recv(100) == hexd
    sock.close()


def test_parse_from_socket():
    rs = PseudoRServer()
    rs.start()
    # now connect to it:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("localhost", PseudoRServer.PORT))
    sock.send(binaryRExpressions.binaryRExpressions['"abc"'])
    assert rparser.rparse(sock) == 'abc'
    sock.close()


def test_parse_from_socket_cleanup_in_case_of_buggy_binary_data():
    rs = PseudoRServer()
    rs.start()
    # now connect to it:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("localhost", PseudoRServer.PORT))
    sock.send('\x01\x00\x99\x00\x50\x00\x00\x00')
    py.test.raises(ValueError, rparser.rparse, sock)
    # Now try to read from socket, which should be empty. To avoid blocking
    # when reading non-available data set timeout to very small value:
    sock.settimeout(0.1)
    py.test.raises(socket.timeout, sock.recv, 100)
    sock.close()

##############################################################

def compareArrays(arr1, arr2):
    def _compareArrays(arr1, arr2):
        assert arr1.shape == arr2.shape
        for idx in range(len(arr1)):
            if isinstance(arr1[idx], ndarray):
                _compareArrays(arr1[idx], arr2[idx])
            else:
                assert arr1[idx] == arr2[idx]
    try:
        _compareArrays(arr1, arr2)
    except TypeError:  #AssertionError:
        return False
    return True


def rExprTester(rExpr, pyExpr, rBinExpr):
    '''
    @Brief  Actual test function called via py.test and the generator "test_rExprGenerator() above.
    @Param  rExpr    <string>             The r expression from r2pyExpressions above
    @Param  pyExpr   <python expression>  The python expression from r2pyExpressions above
    @Param  rBinExpr <string>             rExpr translated by r into its binary (network) representation
    '''
    qTypeCode = struct.unpack('b', rBinExpr[8])[0]
    #
    v = rparser.rparse(rBinExpr, atomicArray=False)
    if isinstance(v, ndarray):
        compareArrays(v, pyExpr)
    elif v.__class__.__name__ == 'TaggedList':
        # do comparision of string representation for now ...
        assert repr(v) == repr(pyExpr)
    else:
        assert v == pyExpr
        
    # assert rserializer.rserialize(pyExpr, asRexp=True, messageCode=messageCode) == rBinExpr
    assert rserializer.rSerializeResponse(pyExpr) == rBinExpr


def hexString(aString):
    'convert a binary string in its hexadecimal representation, like "\x00\x01..."'
    return ''.join([r'\x%02x' % ord(c) for c in aString])

def createBinaryRExpressions():
    '''
    Translates r-expressions from r2pyExpressions into their binary network representations.
    The results will be stored in a python module called "binaryRExpressions.py" which
    is then imported by this module for checking whether the rparser and the rserializer
    produce correct results.
    Running this module requires that R is accessible through PATH.
    '''
    import subprocess, socket, time
    RPORT = 6311
    # Start Rserve
    rProc = subprocess.Popen(['R', 'CMD', 'Rserve.dbg', '--no-save'], stdout=open('/dev/null'))
    # wait a moment until Rserve starts listening on RPORT
    time.sleep(1.0)
    #import pdb;pdb.set_trace()
    
    try:
        # open a socket connection to Rserve
        r = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        r.connect(('', RPORT))
        
        hdr = r.recv(1024)
        assert hdr.startswith('Rsrv01') # make sure we are really connected with rserv
        
        # Create the result file, and write some preliminaries as well as correct code for a dictionary
        # holding the results from calls to Rserve:
        fp = open('binaryRExpressions.py', 'w')
        fp.write("# This file is autogenerated from %s\n" % __file__)
        fp.write("# It contains the translation of r expressions into their \n"
                 "# (network-) serialized representation.\n\n")
        fp.write("binaryRExpressions = {\n")
        for rExpr, pyExpr in r2pyExpressions:
            # make a call to Rserve, sending a valid r expression and then reading the
            # result from the socket:
            # First send header, containing length of data packet part:
            l = len(rExpr)
            # The data packet contains trailing padding zeros to be always a multiple of 4 in length:
            multi4Len = l + (4-divmod(l, 4)[1])
            hdr = '\x03\x00\x00\x00' + struct.pack('<i', 4 + multi4Len) + 8*'\x00'
            # compute data:
            stringHeader = struct.pack('B', rtypes.DT_STRING) + struct.pack('<i', multi4Len)[:3]
            data = stringHeader + rExpr + (multi4Len-l)*'\x00'
            if DEBUG:
                print 'For pyExpr %s sending call to R:\n%s' % (pyExpr, repr(hdr+data))
            r.send(hdr)
            r.send(data)
            time.sleep(0.1)
            binRExpr = r.recv(1024)
            if DEBUG:
                print 'As result received:\n%s\n' % (repr(binRExpr))
            fp.write("    '%s': '%s',\n" % (rExpr, hexString(binRExpr)))
        fp.write("    }\n")
        r.close()
    finally:
        rProc.terminate()  # this call is only available in python2.6 and above




class PseudoRServer(threading.Thread):
    'pseudo rserver, just returning everything received through the network connection'
    #
    PORT = 8888
    #
    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", self.PORT))
        s.listen(1)
        conn, addr = s.accept()
        while 1:
            #print 'PseudoServer waiting for data'
            data = conn.recv(1024)
            if not data:
                break
            #print 'PseudoServer received and sent %d bytes' % len(data)
            conn.send(data)
        s.close()



if __name__ == '__main__':
    createBinaryRExpressions()
else:
    try:
        import binaryRExpressions
    except ImportError:
        # it seems like the autogenerated module is not there yet. Create it, and then import it:
        print 'Cannot import binaryRExpressions, rebuilding them'
        createBinaryRExpressions()
        import binaryRExpressions
