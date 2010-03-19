import socket, time
###
import rtypes
from rexceptions import RConnectionRefused, REvalError, PyRserveClosed
from rserializer import rEval, rAssign
from rparser import rparse

RSERVEPORT = 6311
DEBUG = False


def rconnect(host='', port=RSERVEPORT):
#    if host in (None, ''):
#        # On Win32 it seems that passing an empty string as 'localhost' does not work
#        # So just to be sure provide the full local hostname if None or '' were passed.
#        host = socket.gethostname()
    assert port is not None, 'port number must be given'
    return RConnector(host, port)


def checkIfClosed(func):
    def decoCheckIfClosed(self, *args, **kw):
        if self.isClosed:
            raise PyRserveClosed('Connection to Rserve already closed')
        return func(self, *args, **kw)
    return decoCheckIfClosed
    


class RConnector(object):
    '@brief Provides a network connector to an Rserve process'
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connect()
        self.r = RNameSpace(self)
        self.ref = RNameSpaceReference(self)
        
    def __repr__(self):
        txt = 'Closed handle' if self.isClosed else 'Handle'
        return '<%s to Rserve on %s:%s>' % (txt, self.host or 'localhost', self.port)

    @property
    def isClosed(self):
        return self.__closed

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
        except socket.error:
            raise RConnectionRefused('Connection denied, server not reachable or not accepting connections')
        time.sleep(0.2)
        hdr = self.sock.recv(1024)
        self.__closed = False
        if DEBUG:
            print 'received hdr %s from rserve' % hdr
        assert hdr.startswith('Rsrv01') # make sure we are really connected with rserv
        # TODO: possibly also do version checking here to make sure we understand the protocol...

    @checkIfClosed
    def close(self):
        '@brief Close network connection to rserve'
        self.sock.close()
        self.__closed = True
        
    @checkIfClosed
    def __call__(self, aString):
        return self.eval(aString)
        
    def _reval(self, aString):
        rEval(aString, fp=self.sock)
        
    @checkIfClosed
    def eval(self, aString):
        '@brief Evaluate a string expression through Rserve and return the result transformed into python objects'
        if type(aString) != str:
            raise TypeError('Only string evaluation is allowed')
        self._reval(aString)
        if DEBUG:
            # Read entire data into memory en block, it's easier to debug
            src = self.receive()
            print 'Raw response:', repr(src)
        else:
            src = self.sock.makefile()
        try:
            return rparse(src)
        except REvalError, msg:
            # R has reported an evaulation error, so let's obtain a descriptive explanation
            # about why the error has occurred. R allows to retrieve the error message
            # of the last exception via a built-in function called 'geterrmessage()'.
            errorMsg = self.eval('geterrmessage()').strip()
            raise REvalError(errorMsg)
            
    @checkIfClosed
    def _receive(self):
        '@brief Receive the result from a previous call to rserve.'
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
        '@brief Convert a python object into an RExp and bind it to a variable called "name" in the R namespace'
        rAssign(name, o, self.sock)
        # Rserv sends an emtpy confirmation message, or error message in case of an error.
        # rparse() will raise an Exception in the latter case.
        rparse(self.sock)

    @checkIfClosed
    def getRexp(self, name):
        '@brief Retrieve a Rexp stored in a variable called "name"'
        return self.eval(name)
        
    @checkIfClosed
    def callFunc(self, name, *args, **kw):
        '''
        @brief  make a call to a function "name" through Rserve
        @detail positional and keyword arguments are first stored as local variables in 
                the R namespace and then delivered to the function.
        @result Whatever the result of the called function is.
        '''
        if name == 'rm':
            # SPECIAL HANDLING FOR "rm()":
            # Calling "rm" with real values instead of reference to values works, however
            # it doesn't produce the desired effect (it only removes our temporaily created
            # variables). To avoid confusion for the users a check is applied here to make
            # sure that "args" only contains variable or function references (proxies) and
            # NOT values!
            assert filter(lambda x:not isinstance(x, RBaseProxy), args) == (), \
                   'Only references to variables or functions allowed for "rm()"'
        
        argNames = []
        for idx, arg in enumerate(args):
            if isinstance(arg, RBaseProxy):
                argName = arg.name
            else:
                argName = 'arg_%d_' % idx
                self.setRexp(argName, arg)
            argNames.append(argName)
        for key, value in kw.items():
            if isinstance(value, RBaseProxy):
                argName = value.name
            else:
                argName = 'kwarg_%s_' % key
                self.setRexp(argName, value)
            argNames.append('%s=%s' % (key, argName))
        return self.eval(name+'(%s)' % ', '.join(argNames))

    @checkIfClosed
    def assign(self, aDict):
        '@brief Assign all items of the dictionary to the default R namespace'
        for k, v in aDict.items():
            setRexp(k, v)

    @checkIfClosed
    def isFunction(self, name):
        '@Checks whether given name references an existing function in R'
        return self.eval('is.function(%s)' % name)


class RNameSpace(object):
    'An instance of this class serves as access point to the default namesspace of an Rserve connection'
    def __init__(self, rconn):
        self.__dict__['_rconn'] = rconn
        
    def __setattr__(self, name, o):
        '@brief Assign an rExpr to a variable called "name"'
        self._rconn.setRexp(name, o)

    def __getattr__(self, name):
        '@brief Either retrieve Rexp stored in a variable called "name" or make call to function called "name"'
        realname = name[1:] if name.startswith('_') else name
        try:
            isFunction = self._rconn.isFunction(realname)
        except:
            # an error is only raised if neither such a function or variable exists at all!
            raise NameError('no such variable or function "%s" defined in Rserve' % realname)
        if isFunction:
            return RFuncProxy(realname, self._rconn)
        elif name.startswith('_'):
            return RVarProxy(realname, self._rconn)
        else:
            return self._rconn.getRexp(name)


class RNameSpaceReference(object):
    'Provides references to R objects (a proxy), NOT directly to their values'
    def __init__(self, rconn):
        self.__dict__['_rconn'] = rconn
        
    def __getattr__(self, name):
        '@brief Returns either a reference proxy to a variable to to a function'
        try:
            isFunction = self._rconn.isFunction(name)
        except:
            # an error is only raised if neither such a function or variable exists at all!
            raise NameError('no such variable or function "%s" defined in Rserve' % name)
        if isFunction:
            return RFuncProxy(name, self._rconn)
        else:
            return RVarProxy(name, self._rconn)



class RBaseProxy(object):
    'Proxy for a reference to a variable or function in R. Do not use this directly, only its subclasses'
    def __init__(self, name, rconn):
        self.name = name
        self.rconn = rconn

    

class RVarProxy(RBaseProxy):
    'Proxy for a reference to a variable in R'
    def __repr__(self):
        return '<RVarProxy to variable "%s">' % self.name

    def value(self):
        return self.rconn.getRexp(self.name)
        


class RFuncProxy(RBaseProxy):
    'Proxy for function calls to Rserve'
    def __repr__(self):
        return '<RFuncProxy to function "%s">' % self.name
        
    def __call__(self, *args, **kw):
        return self.rconn.callFunc(self.name, *args, **kw)

    @property
    def __doc__(self):
        try:
            d = self.rconn.eval('readLines(as.character(help(%s)))' % self.name)
        except REvalError:
            # probably no help available, unfortunately there is no specific code for this...
            return None
        helpstring = '\n'.join(d)
        helpstring = helpstring.replace('_\x08', '')
        return helpstring

    def help(self):
        print self.__doc__




if __name__ == '__main__':
    import os, readline, atexit
    # Setup history and readline facility for remote q:
    histfile = os.path.join(os.environ['HOME'], '.pyhistory')
    try:
        readline.read_history_file(histfile)
    except IOError:
        pass
    atexit.register(readline.write_history_file, histfile)

    conn = rconnect()
    print '''"conn" is your handle to rserve. Type e.g. "conn('1')" for string evaluation.'''
    #r('x<-1:20; y<-x*2; lm(y~x)')
    sc = open('../testData/test-script.R').read()
    v = conn(sc)
    open('r-test-png.png', 'w').write(v[3])
    conn.r.v = 'abc'
    conn('func0 <- function() { 3 }')
    conn('func1 <- function(a1) { a1 }')
    conn('func2 <- function(a1, a2) { list(a1, a2) }')
    conn('funcKW <- function(a1=1, a2=4) { list(a1, a2) }')
    conn('squared<-function(t) t^2')

