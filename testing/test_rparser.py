import sys, datetime
###
import numpy, py
###
sys.path.insert(0, '..')
from pyRserve import rtypes, rserializer, rconn
from pyRserve.misc import PY3
from pyRserve.rexceptions import REvalError
from pyRserve.taggedContainers import TaggedList, TaggedArray

from testtools import start_pyRserve, compareArrays


conn = None  # will be set to Rserve-connection in setup_module()

def setup_module(module):
    module.rProc = start_pyRserve()
    module.conn = rconn.connect()          # <---- THIS CREATES A MODULE-WIDE CONNECTION OBJECT TO RSERVE
    # create an 'ident' function which just returns its argument. Needed for testing below.
    module.conn.r(('ident <- function(v) { v }'))

def teardown_module(module):
    try:
        module.rProc.terminate()
        #time.sleep(0.5)
        #if not module.rProc.poll():
        #    module.rProc.kill()
    except AttributeError:
        # probably Rserv process did not startup so the rProc object is not available.
        pass

######################################
### Test strings
def test_eval_strings():
    """Test plain string, byte-strings, unicodes (depending on Python version)"""
    assert conn.r("''") == ''
    assert conn.r("'abc'") == 'abc'
    if PY3:
        # make sure also byte-strings are handled successfully in Python3.x
        assert conn.r(b"'abc'") == 'abc'
    else:
        # make sure also unicode strings are handled successfully in Python2.x
        # Since u'abc' would raise a SyntaxError when this module is loaded in Py3 we have to create the unicode
        # string via eval at runtime (only when Py2 is being used):
        unicode_str = eval("""u'"abc"'""")
        assert type(unicode_str) is unicode
        assert conn.r(unicode_str) == 'abc'

        # test via call to ident function with single argument:
        assert conn.r.ident(eval("u'abc'")) == 'abc'

    # test via call to ident function with single argument:
    assert conn.r.ident('abc') == 'abc'

def test_eval_string_arrays():
    """Test for string arrays"""
    assert compareArrays(conn.r("'abc'", atomicArray=True), numpy.array(['abc']))
    assert compareArrays(conn.r("c('abc', 'def')"), numpy.array(['abc', 'def']))

    # test via call to ident function with single argument:
    assert compareArrays(conn.r.ident(numpy.array(['abc', 'def'])), numpy.array(['abc', 'def']))

### Test integers

def test_eval_integers():
    """Test different types and sizes of integers. Note that R converts all integers into floats"""
    res = conn.r("0")
    assert res == 0.0
    assert type(res) is float

    assert conn.r("1") == 1.0

    #### Create real integers in R:
    res = conn.r('as.integer(c(1))')
    assert res == 1
    assert type(res) == int

    # test via call to ident function with single argument:
    assert conn.r.ident(5) == 5

def test_eval_long():
    """Test long integers. Going beyond sys.maxsize works with eval() because in R all integers are converted
    to floats right away. However sending a long as functional parameter should raise a NotImplementedError if
    its value is outside the normal integer range (i.e. sys.maxsize).
    """
    assert conn.r("%d" % sys.maxsize) == sys.maxsize
    assert conn.r("%d" % (sys.maxsize*2)) == sys.maxsize*2  # these are long integers, handled as floats in R via eval()

    # The syntax like 234L only exists in Python2! So use long in Py2. in Python3 everything is of type <int>
    # Send a long value which is still within below the sys.maxsize. It it automatically converted to a normal int
    # in the rserializer and hence should work fine:
    toLong = int if PY3 else long  # No 'long' function in PY3
    assert conn.r.ident(toLong(123))

    # Here comes the problem - there is no native 64bit integer on the R side, so this should raise a ValueError
    py.test.raises(ValueError, conn.r.ident, sys.maxsize*2)

def test_eval_integer_arrays():
    """Test integer arrays. The result from R is actually always a numpy float array"""
    assert compareArrays(conn.r("266", atomicArray=True), numpy.array([266]))
    assert compareArrays(conn.r("c(55, -35)"), numpy.array([55.0, -35.0]))
    res = conn.r("c(55, -35)")
    assert isinstance(res, numpy.ndarray)
    assert res.dtype == numpy.float

    #### Create real integer arrays in R:
    res = conn.r('as.integer(c(1, 5))')
    assert compareArrays(res, numpy.array([1, 5]))
    assert res.dtype == numpy.int

    # test via call to ident function with single argument:
    assert compareArrays(conn.r.ident(numpy.array([1, 5])), numpy.array([1, 5]))

def test_eval_long_arrays():
    """est calling with a long array where all values are smaller than sys.maxsize. Such an array is internally
    handled as a 32bit integer array and hence should work/
    """
    toLong = int if PY3 else long  # No 'long' function in PY3
    arr64 = numpy.array([-sys.maxsize, toLong(5)], dtype=numpy.int64)
    assert compareArrays(conn.r.ident(arr64), arr64)

    # Here again comes the problem: a int64 array with values beyong sys.maxsize. This should raise a valueerror:
    arr64big = numpy.array([toLong(-32000056789), toLong(5)], dtype=numpy.int64)
    py.test.raises(ValueError, conn.r.ident, arr64big)

### Test floats

def test_eval_floats():
    """Test different types and sizes of floats"""
    res = conn.r("0.0")
    assert res == 0.0
    assert type(res) is float

    assert conn.r("1.0") == 1.0
    assert conn.r("c(1.0)") == 1.0
    assert conn.r("-746586.56") == -746586.56

    # test via call to ident function with single argument:
    assert conn.r.ident(5.5) == 5.5

def test_eval_float_arrays():
    """Test float arrays"""
    assert compareArrays(conn.r("266.5", atomicArray=True), numpy.array([266.5]))
    assert compareArrays(conn.r("c(55.2, -35.7)"), numpy.array([55.2, -35.7]))
    res = conn.r("c(55.5, -35.5)")
    assert isinstance(res, numpy.ndarray)
    assert res.dtype == numpy.float

    # test via call to ident function with single argument:
    assert compareArrays(conn.r.ident(numpy.array([1.7, 5.6])), numpy.array([1.7, 5.6]))

### Test complex numbers

def test_eval_complex():
    """Test different types and sizes of complex numbers"""
    res = conn.r("complex(real = 0, imaginary = 0)")
    assert res == (0+0j)
    assert type(res) is complex

    assert conn.r("complex(real = 5.5, imaginary = -3.3)") == 5.5-3.3j

    # test via call to ident function with single argument:
    assert conn.r.ident(5.5-3.3j) == 5.5-3.3j

def test_eval_complex_arrays():
    """Test complex number arrays"""
    res = conn.r("complex(real = 5.5, imaginary = 6.6)", atomicArray=True)
    assert compareArrays(res, numpy.array([(5.5+6.6j)]))
    assert isinstance(res, numpy.ndarray)
    assert res.dtype == numpy.complex

    # test via call to ident function with single argument:
    arr = numpy.array([(5.5+6.6j), (-3.0-6j)])
    assert compareArrays(conn.r.ident(arr), arr)

### Test boolean values

def test_eval_bool():
    """Test boolean values"""
    res = conn.r('TRUE')
    assert res == True
    assert type(res) == bool
    assert conn.r('FALSE') == False

    # test via call to ident function with single argument:
    assert conn.r.ident(True) == True

def test_eval_bool_arrays():
    """Test boolean arrays"""
    res = conn.r('TRUE', atomicArray=True)
    assert compareArrays(res, numpy.array([True]))
    assert res.dtype == numpy.bool
    assert compareArrays(conn.r('c(TRUE, FALSE)'), numpy.array([True, False]))

    # test via call to ident function with single argument:
    assert compareArrays(conn.r.ident(numpy.array([True, False, False])), numpy.array([True, False, False]))

### Test null value
def test_null_value():
    """Test NULL value, which is None in Python"""
    assert conn.r('NULL') is None
    assert conn.r.ident(None) is None

### Test list function

def test_lists():
    """Test lists which directtly translate into Python lists"""
    assert conn.r('list()') == []
    # with strings
    assert conn.r('list("otto")') == ['otto']
    assert conn.r('list("otto", "amma")') == ['otto', 'amma']
    # with numbers, same type and mixed
    assert conn.r('list(1)') == [1]
    assert conn.r('list(1, 5)') == [1, 5]
    assert conn.r('list(1, complex(real = 5.5, imaginary = -3.3))') == [1, 5.5-3.3j]

    # make a Python-style call to the list-function:
    assert conn.r.list(1, 2, 5) == [1, 2, 5]

    # test via call to ident function with single argument:
    assert conn.r.ident([1, 2, 5]) == [1, 2, 5]

def test_tagged_lists():
    """Tests 'tagged' lists, i.e. lists which allow to address their items via name, not only via index.
    Those R lists are translated into 'TaggedList'-objects in Python.
    """
    res = conn.r('list(husband="otto")')
    assert res == TaggedList([("husband", "otto")])
    # a mixed list, where the 2nd item has no tag:

    exp_res = TaggedList([("n","Fred"), ("v", 2.0), ("c_ages", numpy.array([1.0, 2.0]))])
    res = conn.r('list(n="Fred", v=2, c_ages=c(1, 2))')
    assert repr(res) == repr(exp_res)                     # do string comparison because of complex nested data!

    # test via call to ident function with single argument:
    assert repr(conn.r.ident(exp_res)) == repr(exp_res)   # do string comparison because of complex nested data!

    # NOTE: The following fails in the rserializer because of the missing tag of the 2nd element:  <<<<--------- TODO!!
    # conn.r.ident(TaggedList([("n","Fred"), 2.0, ("c_ages", 5.5)])

### Test more numpy arrays
### Many have been test above, but generally only 1-d arrays. Let's look at arrays with higher dimensions

def test_2d_array_c_order():
    """Arrays can be returned with data in C-order, or Fortran-order. C-order is the default, and used in this test"""
    arr = numpy.array([[1,2,3], [4,5,6]])
    res = conn.r.ident(arr)
    assert compareArrays(res, arr)
    assert res.shape == arr.shape

    # create a 2d array directly in R and compare it again:
    conn.r('arr = c(1, 2, 3, 4, 5, 6)')
    conn.r('dim(arr) = c(2, 3)')
    assert compareArrays(conn.r.arr, arr)


def test_2d_array_fortran_order():
    """Arrays can be returned with data in C-order, or Fortran-order. fortran-order is checked here"""
    # create separate Rserve connection with arrayOrder set to Fortran
    c = rconn.connect(arrayOrder='F')   # also create ident function on server side
    c.r(('ident <- function(v) { v }'))
    arr = numpy.array([[1,2,3], [4,5,6]])
    res = c.r.ident(arr)
    fortran_arr = numpy.array([[1, 4], [2, 5], [3, 6]])
    assert compareArrays(res, fortran_arr)
    assert res.shape == fortran_arr.shape

def test_tagged_array():
    res = conn.r('c(a=1.,b=2.,c=3.)')
    exp_res = TaggedArray.new(numpy.array([1., 2., 3.,]), ['a', 'b', 'c'])
    assert compareArrays(res, exp_res)
    assert res.keys() == exp_res.keys()  # compare the tags of both arrays

### Test evaluation of some R functions

def test_eval_sequence():
    # first string evaluate of R expression:
    res = conn.r('seq(1, 5)')
    assert compareArrays(res, numpy.array(range(1, 6)))
    assert res.dtype == numpy.int32

    # now make Python-style call to the R function:
    assert compareArrays(conn.r.seq(1, 5), numpy.array(range(1, 6)))


def test_eval_polyroot():
    # first string evaluate of R expression:
    res = conn.r('polyroot(c(-39.141,151.469,401.045))')
    exp_res = numpy.array([ 0.1762039 +1.26217745e-29j, -0.5538897 -1.26217745e-29j])
    assert compareArrays(res, exp_res)

    # now make Python-style call to the R function:
    assert compareArrays(conn.r.polyroot(conn.r.c(-39.141,151.469, 401.045)), exp_res)

def test_eval_very_convoluted_function_result():
    """The result of this call is a highly nested data structure. Have fun on evaluation it!"""
    res = conn.r('x<-1:20; y<-x*2; lm(y~x)')
    assert res.__class__ == TaggedList
    # check which tags the TaggedList has:
    assert res.keys == ['coefficients', 'residuals', 'effects', 'rank', 'fitted.values', 'assign', 'qr', 'df.residual',
                        'xlevels', 'call', 'terms', 'model']
    assert compareArrays(res['coefficients'], TaggedArray.new(numpy.array([-0.,  2.]), ['(Intercept)', 'x']))
    # ... many more tags could be tested here ...

### Some more tests
def test_rAssign_method():
    'test "rAssign" class method of RSerializer'
    hexd = b'\x20\x00\x00\x00\x14\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x04\x00\x00\x76\x00'\
           b'\x00\x00\x0a\x08\x00\x00\x20\x04\x00\x00\x01\x00\x00\x00'
    assert rserializer.rAssign('v', 1) == hexd

    # now assign a value via the connector:
    conn.r.aaa = 'a123'
    assert conn.r.aaa == 'a123'


def test_rEval_method():
    hexd = b'\x03\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x04\x00\x00\x61\x3d\x31\x00'
    assert rserializer.rEval('a=1') == hexd


def test_serialize_DT_INT():
    hexd = b'\x03\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x04\x00\x007\x00\x00\x00'
    s = rserializer.RSerializer(rtypes.CMD_eval)
    s.serialize(55, dtTypeCode=rtypes.DT_INT)
    res = s.finalize()
    assert hexd == res


def test_serialize_unsupported_object_raises_exception():
    # datetime objects are not yet supported, so an exception can be expected
    py.test.raises(NotImplementedError, conn.r.ident, datetime.date.today())


def test_eval_illegal_variable_lookup():
    """Calling an invalid variable lookup should result in a proper exception. Also the connector should be still
    usable afterwards.
    """
    try:
        conn.r('x')
    except REvalError as msg:
        assert str(msg) == "Error: object 'x' not found"
    # check that connection still works:
    assert conn.r('1') == 1

def test_eval_illegal_R_statement():
    """Calling an R statement lookup should result in a proper exception. Also the connector should be still
    usable afterwards.
    """
    try:
        conn.r('-%r\0/455')
    except REvalError as msg:
        assert str(msg) == ""  # unforunately this does not return a proper error message
    # check that connection still works:
    assert conn.r('1') == 1

#
#def test_serialize_into_socket():
#    rs = PseudoRServer()
#    rs.start()
#    # now connect to it:
#    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#    sock.connect(("localhost", PseudoRServer.PORT))
#    hexd = b'\x03\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x04\x00\x007\x00\x00\x00'
#    s = rserializer.RSerializer(rtypes.CMD_eval, fp=sock)
#    s.serialize(55, dtTypeCode=rtypes.DT_INT)
#    s.finalize()
#    try:
#        assert sock.recv(100) == hexd
#    finally:
#        sock.close()
#
#
#def test_parse_from_socket():
#    rs = PseudoRServer()
#    rs.start()
#    time.sleep(0.5)
#    # now connect to it:
#    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#    sock.connect(("localhost", PseudoRServer.PORT))
#    sock.send(binaryRExpressions.binaryRExpressions['"abc"'])
#    try:
#        assert rparser.rparse(sock) == 'abc'
#    finally:
#        sock.close()
#        rs.close()
#
#
#def test_parse_from_socket_cleanup_in_case_of_buggy_binary_data():
#    rs = PseudoRServer()
#    rs.start()
#    # now connect to it:
#    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#    sock.connect(("localhost", PseudoRServer.PORT))
#    sock.send(b'\x01\x00\x99\x00\x50\x00\x00\x00')
#    py.test.raises(ValueError, rparser.rparse, sock)
#    # Now try to read from socket, which should be empty. To avoid blocking
#    # when reading non-available data set timeout to very small value:
#    sock.settimeout(0.2)
#    try:
#        py.test.raises(socket.timeout, sock.recv, 100)
#    finally:
#        sock.close()
#
###############################################################
#
#
#
#def rExprTester(rExpr, pyExpr, rBinExpr):
#    '''
#    @Brief  Actual test function called via py.test and the generator "test_rExprGenerator() above.
#    @Param  rExpr    <string>             The r expression from r2pyExpressions above
#    @Param  pyExpr   <python expression>  The python expression from r2pyExpressions above
#    @Param  rBinExpr <string>             rExpr translated by r into its binary (network) representation
#    '''
#    v = rparser.rparse(rBinExpr, atomicArray=False)
#    if isinstance(v, ndarray):
#        compareArrays(v, pyExpr)
#    elif v.__class__.__name__ == 'TaggedList':
#        # do comparison of string representation for now ...
#        assert repr(v) == repr(pyExpr)
#    else:
#        assert v == pyExpr
#
#    # serialize parsed rBinExpr back to binary data stream and check that it is identical to the original value:
#    assert rserializer.rSerializeResponse(v) == rBinExpr
#
#
#
#def createBinaryRExpressions():
#    '''
#    Translates r-expressions from r2pyExpressions into their binary network representations.
#    The results will be stored in a python module called "binaryRExpressions.py" which
#    is then imported by this module for checking whether the rparser and the rserializer
#    produce correct results.
#    Running this module requires that R is accessible through PATH.
#    '''
#    import subprocess, socket, time
#    RPORT = 6311
#    # Start Rserve
#    rProc = subprocess.Popen(['R', 'CMD', 'Rserve.dbg', '--no-save'], stdout=open('/dev/null'))
#    # wait a moment until Rserve starts listening on RPORT
#    time.sleep(1.0)
#
#    try:
#        # open a socket connection to Rserve
#        r = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        r.connect(('', RPORT))
#
#        hdr = r.recv(1024)
#        assert hdr.startswith(b'Rsrv01') # make sure we are really connected with rserv
#
#        # Create the result file, and write some preliminaries as well as correct code for a dictionary
#        # holding the results from calls to Rserve:
#        fp = open('binaryRExpressions.py', 'w')
#        fp.write("# This file is autogenerated from %s\n" % __file__)
#        fp.write("# It contains the translation of r expressions into their \n"
#                 "# (network-) serialized representation.\n\n")
#        fp.write("binaryRExpressions = {\n")
#        for rExpr, pyExpr in r2pyExpressions:
#            # make a call to Rserve, sending a valid r expression and then reading the
#            # result from the socket:
#            # First send header, containing length of data packet part:
#            l = len(rExpr)
#            # The data packet contains trailing padding zeros to be always a multiple of 4 in length:
#            multi4Len = l + (4-divmod(l, 4)[1])
#            hdr = b'\x03\x00\x00\x00' + struct.pack('<i', 4 + multi4Len) + 8*b'\x00'
#            # compute data:
#            stringHeader = struct.pack('B', rtypes.DT_STRING) + struct.pack('<i', multi4Len)[:3]
#            data = stringHeader + byteEncode(rExpr) + (multi4Len-l)*b'\x00'
#            if DEBUG:
#                print('For pyExpr %s sending call to R:\n%s' % (pyExpr, repr(hdr+data)))
#            r.send(hdr)
#            r.send(data)
#            time.sleep(0.1)
#            binRExpr = r.recv(1024)
#            if DEBUG:
#                print('As result received:\n%s\n' % (repr(binRExpr)))
#            fp.write("    '%s': '%s',\n" % (rExpr, hexString(binRExpr)))
#        fp.write("    }\n")
#        r.close()
#    finally:
#        rProc.terminate()  # this call is only available in python2.6 and above
#
#
#
#
#class PseudoRServer(threading.Thread):
#    'pseudo rserver, just returning everything received through the network connection'
#    #
#    PORT = 8888
#    #
#    def run(self):
#        s = self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#        s.bind(("", self.PORT))
#        s.listen(1)
#        conn, addr = s.accept()
#        while 1:
#            data = conn.recv(1024)
#            if not data:
#                break
#                #print 'PseudoServer received and sent %d bytes' % len(data)
#            conn.send(data)
#        s.close()
#
#    def close(self):
#        self.s.close()
#
#
#if __name__ == '__main__':
#    createBinaryRExpressions()
#else:
#    try:
#        from . import binaryRExpressions
#    except ImportError:
#        # it seems like the autogenerated module is not there yet. Create it, and then import it:
#        print('Cannot import binaryRExpressions, rebuilding them')
#        createBinaryRExpressions()
#        from . import binaryRExpressions
