# -*- coding: utf-8 -*-
"""
Module providing functionality to connect to a running Rserve instance
"""
import socket
import time
import pydoc

from . import rtypes
from .rexceptions import RConnectionRefused, REvalError, PyRserveClosed
from .rserializer import rEval, rAssign, rSerializeResponse, rShutdown
from .rparser import rparse, OOBMessage
from .misc import hexString

RSERVEPORT = 6311
DEBUG = False


def _defaultOOBCallback(data, code=0):  # noqa
    return None


class OOBCallback(object):
    """Sets up conn with a new callback when entering the `with` block and
    restores the old one when exiting
    """
    def __init__(self, conn, callback):
        self.conn = conn
        self.callback = callback

    def __enter__(self):
        self.old_callback = self.conn.oobCallback
        self.conn.oobCallback = self.callback
        return self.conn

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.oobCallback = self.old_callback


def connect(host='', port=RSERVEPORT, atomicArray=False, defaultVoid=False,
            oobCallback=_defaultOOBCallback):
    """Open a connection to an Rserve instance
    Params:
    - host: provide hostname where Rserve runs, or leave as empty string to
            connect to localhost
    - port: Rserve port number, defaults to 6311
    - atomicArray:
            If True: when a result from an Rserve call is an array with
            a single element that single element
            is returned. Otherwise the array is returned unmodified.
            Default: True
    - arrayOrder:
            The order in which data in multi-dimensional arrays is returned.
            Provide 'C' for c-order, F for fortran. Default: 'C'
    - defaultVoid:
            If True then calls to conn.r('..') don't return a result by default
    - oobCallback:
            Callback to be executed when self.oobSend/oobMessage is called from
            R. The callback receives the submitted data and a user code as
            parameters. If self.oobMessage was used, the result value of the
            callback is sent back to R.
            Default: lambda data, code=0: None (oobMessage will return NULL)
    """
    if host in (None, ''):
        # On Win32 it seems that passing an empty string as 'localhost' does
        # not work. So just to be sure provide the full local hostname if None
        # or '' were passed.
        host = 'localhost'
    assert port is not None, 'port number must be given'
    return RConnector(host, port, atomicArray, defaultVoid, oobCallback)


def checkIfClosed(func):
    def decoCheckIfClosed(self, *args, **kw):
        if self.isClosed:
            raise PyRserveClosed('Connection to Rserve already closed')
        try:
            return func(self, *args, **kw)
        except socket.error as msg:
            if msg.strerror in ['Connection reset by peer', 'Broken pipe']:
                # seems like the connection to Rserve has died, so mark
                # the connection as closed
                self.close()
                raise PyRserveClosed('Connection to Rserve already closed')
            else:
                raise
    return decoCheckIfClosed


class RConnector(object):
    """Provide a network connector to an Rserve process"""
    def __init__(self, host, port, atomicArray, defaultVoid,
                 oobCallback=_defaultOOBCallback):
        self.sock = None
        self.__closed = True
        self.host = host
        self.port = port
        self.atomicArray = atomicArray
        self.defaultVoid = defaultVoid
        self.oobCallback = oobCallback
        self.r = RNameSpace(self)
        self.ref = RNameSpaceReference(self)
        self.connect()

    def __repr__(self):
        txt = 'Closed handle' if self.isClosed else 'Handle'
        return '<%s to Rserve on %s:%s>' % \
               (txt, self.host or 'localhost', self.port)

    @property
    def isClosed(self):
        return self.__closed

    def connect(self):
        self.sock = socket.socket()
        try:
            self.sock.connect((self.host, self.port))
        except socket.error:
            raise RConnectionRefused('Connection denied, server not reachable '
                                     'or not accepting connections')
        time.sleep(0.2)
        hdr = self.sock.recv(1024)
        self.__closed = False
        if DEBUG:
            print('received hdr %s from rserve' % hdr)
        # make sure we are really connected with rserv
        assert hdr.startswith(b'Rsrv01'), \
            'Protocol error with Rserv, obtained invalid header string'
        # TODO: possibly also do version checking here to make sure we
        #       understand the protocol...

    @checkIfClosed
    def close(self):
        """Close network connection to rserve"""
        self.sock.close()
        self.__closed = True

    @checkIfClosed
    def shutdown(self):
        rShutdown(fp=self.sock)
        self.close()

    def _reval(self, aString, void):
        rEval(aString, fp=self.sock, void=void)

    def _rrespond(self, aObj):
        rSerializeResponse(aObj, fp=self.sock)

    @checkIfClosed
    def eval(self, aString, atomicArray=None, void=False):
        """
        Evaluate a string expression through Rserve and return the result
        transformed into python objects
        """
        if not type(aString in rtypes.STRING_TYPES):
            raise TypeError('Only string evaluation is allowed')
        self._reval(aString, void)
        if DEBUG:
            # Read entire data into memory en bloque, it's easier to debug
            src = self._receive()
            print('Raw response: %s' % hexString(src))
        else:
            src = self.sock

        if atomicArray is None:
            # if not specified, use the global default:
            atomicArray = self.atomicArray

        try:
            message = rparse(src, atomicArray=atomicArray)
            # Before the result is returned, 0-∞ OOB messages may be sent
            while isinstance(message, OOBMessage):
                if DEBUG:
                    print('OOB Message received:', message)
                ret = self.oobCallback(message.data, message.userCode)
                if message.type == rtypes.OOB_MSG:
                    self._rrespond(ret)

                if isinstance(src, (str, bytes)):
                    # This is no stream, so we have to cut off data
                    src = src[len(message):]

                message = rparse(src, atomicArray=atomicArray)
            return message
        except REvalError:
            # R has reported an evaluation error, so let's obtain a descriptive
            # explanation about why the error has occurred. R allows to
            # retrieve the error message of the last exception via a built-in
            # function called 'geterrmessage()'.
            errorMsg = self.eval('geterrmessage()').strip()
            raise REvalError(errorMsg)

    @checkIfClosed
    def voidEval(self, aString):
        """
        Evaluate a string expression through Rserve without returning
        any result data
        """
        self.eval(aString, void=True)

    @checkIfClosed
    def _receive(self):
        """Receive the result from a previous call to rserve."""
        raw = self.sock.recv(rtypes.SOCKET_BLOCK_SIZE)
        d = [raw]
        while len(raw) == rtypes.SOCKET_BLOCK_SIZE:
            raw = self.sock.recv(rtypes.SOCKET_BLOCK_SIZE)
            d.append(raw)
        return ''.join(d)

#    @checkIfClosed
#    def _raw(self, *args, **kw):
#        self.send(*args)
#        return self.receive()

    @checkIfClosed
    def setRexp(self, name, o):
        """
        Convert a python object into an RExp and bind it to a variable
        called "name" in the R namespace
        """
        rAssign(name, o, self.sock)
        # Rserv sends an emtpy confirmation message, or error message in case
        # of an error. rparse() will raise an Exception in the latter case.
        rparse(self.sock, atomicArray=self.atomicArray)

    @checkIfClosed
    def getRexp(self, name):
        """Retrieve a Rexp stored in a variable called 'name'"""
        return self.eval(name)

    @checkIfClosed
    def callFunc(self, name, *args, **kw):
        """
        @brief  make a call to a function "name" through Rserve
        @detail positional and keyword arguments are first stored as local
                variables in the R namespace and then delivered to the
                function.
        @result Whatever the result of the called function is.
        """
        if name == 'rm':
            # SPECIAL HANDLING FOR "rm()":
            # Calling "rm" with real values instead of reference to values
            # works, however it doesn't produce the desired effect (it only
            # removes temporaily created variables). To avoid confusion for
            # the users a check is applied here to make sure that "args" only
            # contains variable or function references (proxies) and NOT
            # values!
            assert [x for x in args if not isinstance(x, RBaseProxy)] == (),\
                'Only references to variables or functions allowed for "rm()"'

        argNames = []
        for idx, arg in enumerate(args):
            if isinstance(arg, RBaseProxy):
                argName = arg.__name__
            else:
                # a real python value is passed. Set a value of an artificial
                # variable on the R side, memorize its name for making the
                # actual call to the function below
                argName = 'arg_%d_' % idx
                self.setRexp(argName, arg)
            argNames.append(argName)
        for key, value in kw.items():
            if isinstance(value, RBaseProxy):
                argName = value.__name__
            else:
                argName = 'kwarg_%s_' % key
                self.setRexp(argName, value)
            argNames.append('%s=%s' % (key, argName))
        return self.eval(name+'(%s)' % ', '.join(argNames))

    @checkIfClosed
    def assign(self, aDict):
        """Assign all items of the dictionary to the default R namespace"""
        for k, v in aDict.items():
            self.setRexp(k, v)

    @checkIfClosed
    def isFunction(self, name):
        """Check whether given name references an existing function in R"""
        return self.eval('is.function(%s)' % name)


class RNameSpace(object):
    """
    An instance of this class serves as access point to the default namesspace
    of an Rserve connection
    """
    def __init__(self, rconn):
        self.__dict__['_rconn'] = rconn

    def __setattr__(self, name, o):
        """Assign an rExpr to a variable called 'name'"""
        self._rconn.setRexp(name, o)

    def __getattr__(self, name):
        """
        Retrieve either Rexp stored in a variable called "name" or make call
        to function called 'name'
        """
        realname = name[1:] if name.startswith('_') else name
        try:
            isFunction = self._rconn.isFunction(realname)
        except Exception:
            # an error is only raised if neither such a function or variable
            # exists at all!
            raise NameError('no such variable or function "%s" '
                            'defined in Rserve' % realname)
        if isFunction:
            return RFuncProxy(realname, self._rconn)
        elif name.startswith('_'):
            return RVarProxy(realname, self._rconn)
        else:
            return self._rconn.getRexp(name)

    def __call__(self, aString, atomicArray=None, void=None):
        if void is None:
            void = self._rconn.defaultVoid
        return self._rconn.eval(aString, atomicArray=atomicArray, void=void)


class RNameSpaceReference(object):
    """
    Provide reference to R objects (a proxy), NOT directly to their values
    """
    def __init__(self, rconn):
        self.__dict__['_rconn'] = rconn

    def __getattr__(self, name):
        """Return either a reference proxy to a variable to to a function"""
        try:
            isFunction = self._rconn.isFunction(name)
        except Exception:
            # an error is only raised if neither such a function or variable
            # exists at all!
            raise NameError('no such variable or function "%s" '
                            'defined in Rserve' % name)
        if isFunction:
            return RFuncProxy(name, self._rconn)
        else:
            return RVarProxy(name, self._rconn)


class RBaseProxy(object):
    """
    Proxy for a reference to a variable or function in R.
    Do not use this directly, only its subclasses.
    """
    def __init__(self, name, rconn):
        self.__name__ = name
        self._rconn = rconn


class RVarProxy(RBaseProxy):
    """Proxy for a reference to a variable in R"""
    def __repr__(self):
        return '<RVarProxy to variable "%s">' % self.__name__

    def value(self):
        return self._rconn.getRexp(self.__name__)


class RFuncProxy(RBaseProxy):
    """Proxy for function calls to Rserve"""
    def __repr__(self):
        return '<RFuncProxy to function "%s">' % self.__name__

    def __call__(self, *args, **kw):
        return self._rconn.callFunc(self.__name__, *args, **kw)

    # command to send to R in order to get the help for a function in text
    # format:
    R_HELP = "capture.output(tools:::Rd2txt(utils:::.getHelpFile(help(%s))))"

    @property
    def __doc__(self):
        """
        There are different ways to get the help message from R:
        # The the package db file:
        pkgRdDB = tools:::fetchRdDB(file.path(find.package('base'),
                                              'help', 'base'))
        # show all available topics in the help package:
        names(pkgRdDB)
        # convert the 'lapply' help message to text (from the base package):
        tools::Rd2txt(pkgRdDB[['lapply']])
        # capture this output into a variable:
        a <- capture.output(tools::Rd2txt(pkgRdDB[['lapply']]))
        Disadvantage: One needs to know the package beforehand.

        Better:
        Everything in one line and better (doesn't need to know the pkg):
        a <- capture.output(tools:::Rd2txt(utils:::.getHelpFile(help(sapply))))
        """
        try:
            d = self._rconn.eval(self.R_HELP % self.__name__)
        except REvalError:
            # probably no help available, unfortunately there is no specific
            # code for this...
            return None
        # Join the list of strings:
        helpstring = '\n'.join(d)
        # remove some obscure characters:
        # helpstring = helpstring.replace('_\x08', '')
        return helpstring

    def help(self):
        """Directly page the help message to the terminal (e.g. via less)"""
        pydoc.pager(self.__doc__)

    def __getattr__(self, name):
        """Allow for nested name space calls, e.g. 't.test' """
        if name == '__name__':
            # this is useful for py.test which does some code inspection
            # during runtime
            return self.__name__

        concatName = "%s.%s" % (self.__name__, name)
        try:
            self._rconn.isFunction(concatName)
        except Exception:
            # an error is only raised if neither such a function or variable
            # exists at all!
            raise NameError('no such variable or function "%s" '
                            'defined in R' % concatName)
        return RFuncProxy(concatName, self._rconn)


def _test_main():
    import os
    import readline
    import atexit
    # Setup history and readline facility for remote q:
    histfile = os.path.join(os.environ['HOME'], '.pyhistory')
    try:
        readline.read_history_file(histfile)
    except IOError:
        pass
    atexit.register(readline.write_history_file, histfile)

    conn = connect()
    print('"conn" is your handle to rserve. Type e.g. "conn(\'1\')" '
          'for string evaluation.')
    # r('x<-1:20; y<-x*2; lm(y~x)')
    sc = open('../testData/test-script.R').read()
    v = conn.r(sc)
    open('r-test-png.png', 'w').write(v[3])
    conn.r.v = 'abc'
    conn.r('func0 <- function() { 3 }')
    conn.r('func1 <- function(a1) { a1 }')
    conn.r('func2 <- function(a1, a2) { list(a1, a2) }')
    conn.r('funcKW <- function(a1=1, a2=4) { list(a1, a2) }')
    conn.r('squared<-function(t) t^2')


if __name__ == '__main__':
    _test_main()
