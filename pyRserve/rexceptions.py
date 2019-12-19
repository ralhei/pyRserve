"""
Exception classes for pyRserve
"""


class PyRserveError(Exception):
    pass


class REvalError(PyRserveError):
    """Indicates an error raised by R itself (not by Rserve)"""
    pass


class RConnectionRefused(PyRserveError):
    pass


class RResponseError(PyRserveError):
    pass


class RSerializationError(PyRserveError):
    pass


class PyRserveClosed(PyRserveError):
    pass


class EndOfDataError(PyRserveError):
    pass


class RParserError(PyRserveError):
    pass
