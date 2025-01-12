"""
Module for misc functions and classes.
"""


class FunctionMapper:
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
    return ''.join([r'\x%02x' % c for c in aString])


def byteEncode(aString, encoding='utf-8'):
    # check for __name__ not to get faked by Python2.x!
    if type(aString).__name__ != 'bytes':
        return bytes(aString, encoding=encoding)
    else:
        return aString


def stringEncode(byteData, encoding='utf-8'):
    # check for __name__ not to get faked by Python2.x!
    if type(byteData).__name__ == 'bytes':
        if byteData == b'\xff':
            return None
        return byteData.decode(encoding=encoding)
    else:
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
    byte_string = byteEncode(aString) + b'\0'
    return byte_string + padLen4(byte_string) * b'\0'
