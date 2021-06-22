import sys

# global variable to indicate whether this is Python3 or not:
PY3 = sys.version_info[0] == 3


class FunctionMapper(object):
    """
    This class is used in Lexer, Parser, and Serializer to map IDs
    to functions"""
    def __init__(self, adict):
        self.adict = adict

    def __call__(self, *args):
        def wrap(func):
            for a in args:
                self.adict[a] = func
            return func
        return wrap


def hexString(aString):
    """
    convert a binary string in its hexadecimal representation,
    like '\x00\x01...'
    """
    if PY3:
        # in Py3 iterating over a byte-sequence directly provides the
        # numeric values of the bytes  ...
        return ''.join([r'\x%02x' % c for c in aString])
    else:
        # ... while in Py2 we need to use ord() to convert chars to
        # their numeric values:
        return ''.join([r'\x%02x' % ord(c) for c in aString])


def byteEncode(aString, encoding='utf-8'):
    # check for __name__ not to get faked by Python2.x!
    if PY3 and type(aString).__name__ != 'bytes':
        return bytes(aString, encoding=encoding)
    else:
        if type(aString).__name__.startswith('unicode'):
            return aString.encode('utf-8')
        else:
            return aString


def stringEncode(byteData, encoding='utf-8'):
    # check for __name__ not to get faked by Python2.x!
    if PY3 and type(byteData).__name__ == 'bytes':
        if byteData == b'\xff':
            return None
        # got a real bytes object, must be python3 !
        return byteData.decode(encoding=encoding)
    else:
        # in py2.x there is no real byte-data, it is a string already
        return byteData


def padLen4(aString):
    """
    Calculate how many additional bytes a given string needs to have a length
    of a multiple of 4. A zero-length array is considered a multiple of 4.
    """
    mod = divmod(len(aString), 4)[1]
    return 4-mod if mod else 0


def string2bytesPad4(aString):
    """
    Return a given string converted into bytes, padded with zeros at the end
    to make its length be a multiple of 4.
    A zero-length string is considered a multiple of 4.
    """
    byteString = byteEncode(aString) + b'\0'
    return byteString + padLen4(byteString) * b'\0'
