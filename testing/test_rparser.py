# -*- coding: utf-8 -*-
"""
Unittesting module for rparser
"""
import datetime
###
import numpy
import py
###
from pyRserve import rtypes, rserializer, rconn, rparser
from pyRserve.rconn import RVarProxy, OOBCallback
from pyRserve.misc import PY3
from pyRserve.rexceptions import REvalError
from pyRserve.taggedContainers import TaggedList, TaggedArray
###
from .testtools import start_pyRserve, compareArrays, RPORT

conn = None  # will be set to Rserve-connection in setup_module()


def setup_module(module):
    module.rProc = start_pyRserve()
    # CREATE A MODULE-WIDE CONNECTION OBJECT TO RSERVE
    try:
        module.conn = rconn.connect(port=RPORT)
    except:
        module.rProc.terminate()
        raise
    # create an 'ident' function which just returns its argument.
    # Needed for testing below.
    module.conn.r('ident <- function(v) { v }')


def teardown_module(module):
    try:
        module.conn.close()
        module.rProc.terminate()
    except AttributeError:
        # probably Rserve process did not startup so the rProc object is
        # not available.
        pass


######################################
# ### Test strings

def test_eval_strings():
    """
    Test plain string, byte-strings, unicodes (depending on Python version)
    """
    assert conn.r("''") == ''
    assert conn.r("'abc'") == 'abc'

    # make sure also byte-strings are handled successfully.
    # Makes no difference in PY2, but in PY3 it does:
    assert conn.r(b"'abc'") == 'abc'

    # test via call to ident function with single argument:
    assert conn.r.ident('abc') == 'abc'

    try:
        # make sure also unicode strings are handled successfully in Python2.x
        # Since u'abc' would raise a SyntaxError when this module is loaded
        # in Py3 < 3.3 we have to create the unicode string via eval at
        # runtime:
        unicode_str = eval("""u'"abc"'""")
    except SyntaxError:
        # outdated PY3 version, so just skip the rest
        return

    assert conn.r(unicode_str) == 'abc'

    # test via call to ident function with single argument:
    assert conn.r.ident(eval("u'abc'")) == 'abc'


def test_eval_string_arrays():
    """Test for string arrays"""
    assert compareArrays(conn.r("'abc'", atomicArray=True),
                         numpy.array(['abc']))
    assert compareArrays(conn.r("c('abc', 'def')"),
                         numpy.array(['abc', 'def']))

    # test via call to ident function with single argument:
    assert compareArrays(conn.r.ident(numpy.array(['abc', 'def'])),
                         numpy.array(['abc', 'def']))


def test_eval_unicode_arrays():
    """
    Test for unicode arrays. The ident function should return the
    same array, just not as unicode
    """
    try:
        u1 = eval("u'abc'")
        u2 = eval("u'def'")
    except SyntaxError:
        # Python 3 below 3.3 does not accept the u'' operator,
        # just skip this test!
        return

    # test via call to ident function with single argument:
    assert conn.r.ident(numpy.array([u1])) == 'abc'
    assert compareArrays(conn.r.ident(numpy.array([u1, u2])),
                         numpy.array(['abc', 'def']))


# ### Test integers

def test_eval_integers():
    """
    Test different types and sizes of integers.
    Note that R converts all integers into floats
    """
    res = conn.r("0")
    assert res == 0.0
    assert type(res) is float

    assert conn.r("1") == 1.0

    # ### Create real integers in R:
    res = conn.r('as.integer(c(1))')
    assert res == 1
    assert type(res) == int

    # test via call to ident function with single argument:
    assert conn.r.ident(5) == 5


def test_eval_long():
    """
    Test long integers. Going beyond MAX_INT32 works with eval() because
    in R all integers are converted to floats right away. However sending a
    long as functional parameter should raise a NotImplementedError if
    its value is outside the normal integer range (i.e. MAX_INT32).
    """
    assert conn.r("%d" % rtypes.MAX_INT32) == rtypes.MAX_INT32
    # Next test for long integers, handled as floats in R via eval():
    assert conn.r("%d" % (rtypes.MAX_INT32*2)) == rtypes.MAX_INT32*2

    # The syntax like 234L only exists in Python2! So use long in Py2. I
    # n Python3 everything is of type <int>
    # Send a long value which is still within below the rtypes.MAX_INT32.
    # It it automatically converted to a normal int in the rserializer and
    # hence should work fine:
    toLong = int if PY3 else long  # No 'long' function in PY3
    assert conn.r.ident(toLong(123))

    # Here comes the problem - there is no native 64bit integer on the R side,
    # so this should raise a ValueError
    py.test.raises(ValueError, conn.r.ident, rtypes.MAX_INT32*2)


def test_eval_integer_arrays():
    """
    Test integer arrays. The result from R is actually always a numpy
    float array
    """
    assert compareArrays(conn.r("266", atomicArray=True), numpy.array([266]))
    assert compareArrays(conn.r("c(55, -35)"), numpy.array([55.0, -35.0]))
    res = conn.r("c(55, -35)")
    assert isinstance(res, numpy.ndarray)
    assert res.dtype == numpy.float

    # ### Create real integer arrays in R:
    res = conn.r('as.integer(c(1, 5))')
    assert compareArrays(res, numpy.array([1, 5]))
    assert res.dtype in (numpy.int, numpy.int32)

    # test via call to ident function with single argument:
    assert compareArrays(conn.r.ident(numpy.array([1, 5])),
                         numpy.array([1, 5]))


def test_eval_long_arrays():
    """
    Test calling with a long array where all values are smaller than
    MAX_INT32. Such an array is internally handled as a 32bit integer array
    and hence should work.
    """
    toLong = int if PY3 else long  # No 'long' function in PY3
    # arr64 = numpy.array([rtypes.MIN_INT32, toLong(5)], dtype=numpy.int64)
    # assert compareArrays(conn.r.ident(arr64), arr64)

    # Here again comes the problem: a int64 array with values beyong
    # rtypes.MAX_INT32. This should raise a ValueError:
    arr64big = numpy.array([toLong(-rtypes.MAX_INT32 * 2), toLong(5)],
                           dtype=numpy.int64)
    py.test.raises(ValueError, conn.r.ident, arr64big)


# ### Test floats

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
    assert compareArrays(conn.r("266.5", atomicArray=True),
                         numpy.array([266.5]))
    assert compareArrays(conn.r("c(55.2, -35.7)"), numpy.array([55.2, -35.7]))
    res = conn.r("c(55.5, -35.5)")
    assert isinstance(res, numpy.ndarray)
    assert res.dtype == numpy.float

    # test via call to ident function with single argument:
    assert compareArrays(conn.r.ident(numpy.array([1.7, 5.6])),
                         numpy.array([1.7, 5.6]))


# ### Test complex numbers

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


# ### Test boolean values

def test_eval_bool():
    """Test boolean values"""
    res = conn.r('TRUE')
    assert res is True
    assert type(res) == bool
    assert conn.r('FALSE') is False

    # test via call to ident function with single argument:
    assert conn.r.ident(True) is True


def test_eval_bool_arrays():
    """Test boolean arrays"""
    res = conn.r('TRUE', atomicArray=True)
    assert compareArrays(res, numpy.array([True]))
    assert res.dtype == numpy.bool
    assert compareArrays(conn.r('c(TRUE, FALSE)'), numpy.array([True, False]))

    # test via call to ident function with single argument:
    assert compareArrays(conn.r.ident(numpy.array([True, False, False])),
                         numpy.array([True, False, False]))


def test_empty_boolean_array():
    """Check that zero-length boolean ('logical') array is returned fine"""
    conn.r('empty_bool_arr = as.logical(c())')
    assert compareArrays(conn.r.empty_bool_arr, numpy.array([], dtype=bool))


# ### Test null value

def test_null_value():
    """Test NULL value, which is None in Python"""
    assert conn.r('NULL') is None
    assert conn.r.ident(None) is None


# ### Test list function

def test_lists():
    """Test lists which directtly translate into Python lists"""
    assert conn.r('list()') == []
    # with strings
    assert conn.r('list("otto")') == ['otto']
    assert conn.r('list("otto", "amma")') == ['otto', 'amma']
    # with numbers, same type and mixed
    assert conn.r('list(1)') == [1]
    assert conn.r('list(1, 5)') == [1, 5]
    assert conn.r('list(1, complex(real = 5.5, imaginary = -3.3))') == \
        [1, 5.5-3.3j]

    # make a Python-style call to the list-function:
    assert conn.r.list(1, 2, 5) == [1, 2, 5]

    # test via call to ident function with single argument:
    assert conn.r.ident([1, 2, 5]) == [1, 2, 5]


def test_tagged_lists():
    """
    Tests 'tagged' lists, i.e. lists which allow to address their items via
    name, not only via index.
    Those R lists are translated into 'TaggedList'-objects in Python.
    """
    res = conn.r('list(husband="otto")')
    assert res == TaggedList([("husband", "otto")])
    # a mixed list, where the 2nd item has no tag:

    exp_res = TaggedList([("n", "Fred"), ("v", 2.0),
                          ("c_ages", numpy.array([1.0, 2.0]))])
    res = conn.r('list(n="Fred", v=2, c_ages=c(1, 2))')
    # do string comparison because of complex nested data!
    assert repr(res) == repr(exp_res)

    # test via call to ident function with single argument:
    # do string comparison because of complex nested data!
    assert repr(conn.r.ident(exp_res)) == repr(exp_res)

    # NOTE: The following fails in the rserializer because of the missing tag
    # of the 2nd element:  <<<<--------- TODO!!
    # conn.r.ident(TaggedList([("n","Fred"), 2.0, ("c_ages", 5.5)])


def test_vector_expression():
    """
    Tests for typecode 0x1a XT_VECTOR_EXP - returns the expression content
    as python list
    """
    # first empty expression
    res = conn.r('expression()')
    assert res == []

    # second expression with content
    res = conn.r('expression("1+1")')
    assert res == ['1+1']


# ### Test more numpy arrays
# ### Many have been test above, but generally only 1-d arrays. Let's look at
# ### arrays with higher dimensions

def test_2d_arrays_created_in_python():
    """
    Check that transferring various arrays to R preserves columns, rows,
    and shape.
    """
    bools = [True, False, True, True]
    strings = ['abc', 'def', 'ghi', 'jkl']
    arrays = [
        # next is same as: numpy.array([[1,2,3], [4,5,6]])
        numpy.arange(6).reshape((2, 3), order='C'),
        # next is same as: numpy.array([[1,3,5], [2,4,6]])
        numpy.arange(6).reshape((2, 3), order='F'),
        # next is same as: numpy.array([[True, False], [True, True]])
        numpy.array(bools).reshape((2, 2), order='C'),
        # next is same as: numpy.array([[True, True], [False, True]])
        numpy.array(bools).reshape((2, 2), order='F'),
        numpy.array(strings).reshape((2, 2), order='C'),
        numpy.array(strings).reshape((2, 2), order='F'),
    ]

    for arr in arrays:
        res = conn.r.ident(arr)
        assert res.shape == arr.shape
        assert compareArrays(res, arr)

        # assign array within R namespace and check some cols and rows:
        conn.r.arr = arr
        # check that 2nd row (last row) is equal:
        assert compareArrays(arr[1], conn.r('arr[2,]'))
        # check that 2nd column (middle col) is equal:
        assert compareArrays(arr[:, 1], conn.r('arr[,2]'))


def test_2d_numeric_array_created_in_R():
    """
    Create an array in R, transfer it to python, and check that columns,
    rows, and shape are preserved.
    Note: Arrays in R are always in Fortran order, i.e. first index moves
    fastest.

    The array in R looks like:
         [,1] [,2] [,3]
    [1,]    1    3    5
    [2,]    2    4    6
    """
    arr = conn.r('arr = array(1:6, dim=c(2, 3))')
    assert compareArrays(conn.r.arr, arr)

    # check that 2nd row (last row) is equal:
    assert len(arr[1]) == len(conn.r('arr[2,]')) == 3
    assert compareArrays(arr[1], conn.r('arr[2,]'))

    # check that 2nd column (middle col) is equal:
    assert len(arr[:, 1]) == len(conn.r('arr[,2]')) == 2
    assert compareArrays(arr[:, 1], conn.r('arr[,2]'))


def test_tagged_array():
    res = conn.r('c(a=1.,b=2.,c=3.)')
    exp_res = TaggedArray.new(numpy.array([1., 2., 3.]), ['a', 'b', 'c'])
    assert compareArrays(res, exp_res)
    assert res.keys() == exp_res.keys()  # compare the tags of both arrays


def test_very_large_result_array():
    """Check that a SEXP with XT_LARGE set in header is properly parsed """
    res = conn.r('c(1:9999999)')
    assert res.size == 9999999


def test_eval_void():
    """
    Check that conn.voidEval() does not return any result in contrast to
    conn.eval()
    """
    assert conn.r('a=1') == 1.0
    assert conn.eval('a=1') == 1.0
    assert conn.voidEval('a=1') is None
    assert conn.eval('a=1', void=True) is None
    assert conn.r('a=1', void=True) is None


# ### Test evaluation of some R functions

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
    exp_res = numpy.array([0.1762039 + 1.26217745e-29j,
                           -0.5538897 - 1.26217745e-29j])
    assert compareArrays(res, exp_res)

    # now make Python-style call to the R function:
    assert compareArrays(conn.r.polyroot(conn.r.c(-39.141, 151.469, 401.045)),
                         exp_res)


def test_eval_very_convoluted_function_result():
    """
    The result of this call is a highly nested data structure.
    Have fun on evaluation it!
    """
    res = conn.r('x<-1:20; y<-x*2; lm(y~x)')
    assert res.__class__ == TaggedList
    # check which tags the TaggedList has:
    assert res.keys == ['coefficients', 'residuals', 'effects', 'rank',
                        'fitted.values', 'assign', 'qr', 'df.residual',
                        'xlevels', 'call', 'terms', 'model']
    assert compareArrays(res['coefficients'],
                         TaggedArray.new(numpy.array([-0.,  2.]),
                                         ['(Intercept)', 'x']))
    # ... many more tags could be tested here ...


def test_sapply_with_func_proxy_argument():
    """
    Test calling sapply providing a proxy object to a R function as argument
    """
    res = conn.r.sapply(-5, conn.r.abs)
    assert res == 5


# ### Some more tests

def xtest_parse_s4_result():
    """
    S4 are special objects in R, generated e.g. when creating a database
    connection as shown below:

    in R:
        install.packages('RSQLite')
        install.packages('DBI')

    in Python:
        c.eval("library(RSQLite)")
        c.eval("con <- dbConnect(RSQLite::SQLite(), dbname='testdb')")

    To avoid the dependency of having RSQLite installed for unittesting
    the raw result of the
    """
    raw = '\x01\x00\x01\x00\xbc\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
          '\x0a\xb8\x00\x00\x87\xb4\x00\x00\x15\xb0\x00\x00\x30\x04\x00\x00' \
          '\x16\x00\x00\x00\x13\x04\x00\x00\x49\x64\x00\x00\x22\x08\x00\x00' \
          '\x74\x65\x73\x74\x64\x62\x00\x01\x13\x08\x00\x00\x64\x62\x6e\x61' \
          '\x6d\x65\x00\x00\x24\x08\x00\x00\x01\x00\x00\x00\x01\xff\xff\xff' \
          '\x13\x14\x00\x00\x6c\x6f\x61\x64\x61\x62\x6c\x65\x2e\x65\x78\x74' \
          '\x65\x6e\x73\x69\x6f\x6e\x73\x00\x20\x04\x00\x00\x06\x00\x00\x00' \
          '\x13\x08\x00\x00\x66\x6c\x61\x67\x73\x00\x00\x00\x22\x04\x00\x00' \
          '\x00\x01\x01\x01\x13\x04\x00\x00\x76\x66\x73\x00\xa2\x30\x00\x00' \
          '\x15\x18\x00\x00\x22\x08\x00\x00\x52\x53\x51\x4c\x69\x74\x65\x00' \
          '\x13\x08\x00\x00\x70\x61\x63\x6b\x61\x67\x65\x00\x53\x51\x4c\x69' \
          '\x74\x65\x43\x6f\x6e\x6e\x65\x63\x74\x69\x6f\x6e\x00\x01\x01\x01' \
          '\x13\x08\x00\x00\x63\x6c\x61\x73\x73\x00\x00\x00'
    res = rparser.rparse(raw)
    assert isinstance(res, rparser.S4)


def test_rAssign_method():
    """test "rAssign" class method of RSerializer"""
    hexd = b'\x20\x00\x00\x00\x14\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
           b'\x00\x04\x04\x00\x00\x76\x00\x00\x00\x0a\x08\x00\x00\x20\x04' \
           b'\x00\x00\x01\x00\x00\x00'
    assert rserializer.rAssign('v', 1) == hexd

    # now assign a value via the connector:
    conn.r.aaa = 'a123'
    assert conn.r.aaa == 'a123'


def test_rEval_method():
    """test "rEval" method"""
    hexd = b'\x03\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
           b'\x00\x04\x04\x00\x00\x61\x3d\x31\x00'
    assert rserializer.rEval('a=1') == hexd


def test_serialize_DT_INT():
    hexd = b'\x03\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
           b'\x00\x01\x04\x00\x007\x00\x00\x00'
    s = rserializer.RSerializer(rtypes.CMD_eval)
    s.serialize(55, dtTypeCode=rtypes.DT_INT)
    res = s.finalize()
    assert hexd == res


def test_serialize_unsupported_object_raises_exception():
    # datetime objects are not yet supported, so an exception can be expected
    py.test.raises(NotImplementedError, conn.r.ident, datetime.date.today())


def test_eval_illegal_variable_lookup():
    """
    Calling an invalid variable lookup should result in a proper exception.
    Also the connector should be still usable afterwards.
    """
    try:
        conn.r('x')
    except REvalError as msg:
        assert str(msg) == "Error: object 'x' not found"
    # check that the connection still works:
    assert conn.r('1') == 1


def test_eval_illegal_R_statement():
    """
    Calling an R statement lookup should result in a proper exception.
    Also the connector should be still usable afterwards.
    """
    try:
        conn.r('x-%r\0/455')
    except REvalError:
        pass
    # check that the connection still works:
    assert conn.r('1') == 1


#######################
# some more tests

def test_rvarproxy():
    """A var proxy is accessed via conn.ref"""
    conn.r.a = [1, 2, 3]
    assert conn.ref.a.__class__ == RVarProxy
    assert conn.ref.a.value() == [1, 2, 3]


def test_oob_send():
    """Tests OOB without registering a callback"""
    assert conn.r('self.oobSend("foo")') is True


def test_oob_message():
    """Tests OOB Message. Should not lock up, and without callbacks,
    NULL should be sent back to R. (None → NULL)
    """
    assert conn.r('stopifnot(self.oobMessage("foo") == NULL)') is None


def test_oob_callback():
    """Tests OOB with one registered callback"""
    collect = []

    def collectMSG(data, code=0):
        collect.append((code, data))

    with OOBCallback(conn, collectMSG):
        conn.r('self.oobSend(1)')
        conn.r('self.oobMessage(2, code=10L)')

        assert collect == [(0, 1), (10, 2)]


def test_oob_callback_result():
    """Tests OOB with a registered callback returning a one"""
    with OOBCallback(conn, lambda data, code=0: 1):
        assert conn.r('stopifnot(self.oobMessage(NULL) == 1L)') is None


def test_help_message():
    """Check that a help message is properly delivered from R for a function"""
    help_msg = conn.r.sapply.__doc__
    assert help_msg is not None
    # remove the extra underscore formatting characters from the help message:
    help_msg = help_msg.replace('_\x08', '')
    assert help_msg.startswith('Apply a Function over a List or Vector')
