import socket, time
###
import rtypes
from rexceptions import RConnectionRefused
from rserializer import rserialize
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


class RConnector(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connect()
        
    def __repr__(self):
        return '<Handle to Rserve on %s:%s>' % (self.host or 'localhost', self.port)

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
        except socket.error:
            raise RConnectionRefused('Connection denied, server not reachable or not accepting connections')
        time.sleep(0.2)
        hdr = self.sock.recv(1024)
        if DEBUG:
            print 'received hdr %s from rserve' % hdr
        assert hdr.startswith('Rsrv01') # make sure we are really connected with rserv
        # TODO: possibly also do version checking here to make sure we understand the protocol...

    def close(self):
        '@brief Close network connection to rserve'
        self.sock.close()
        
    def __call__(self, *args, **kw):
        self.send(*args)
        if DEBUG:
            # Read entire data into memory en block, it's easier to debug
            src = self.receive()
            print 'Raw response:', repr(src)
        else:
            src = self.sock.makefile()
        return rparse(src)
        
    def send(self, *args, **kw):
        '''
        @brief Serializes given arguments and sends them to the rserve process.
        @note  The result needs to be received separately (using self.receive())
        '''
        data = rserialize(args[0] if len(args)==1 else args, **kw)
        self.sock.send(data)

    def receive(self):
        '@brief Receive the result from a previous call to rserve.'
        raw = self.sock.recv(rtypes.SOCKET_BLOCK_SIZE)
        d = [raw]
        while len(raw) == rtypes.SOCKET_BLOCK_SIZE:
            raw = self.sock.recv(rtypes.SOCKET_BLOCK_SIZE)
            d.append(raw)
        return ''.join(d)

    def raw(self, *args, **kw):
        self.send(*args)
        return self.receive()


if __name__ == '__main__':
    r = rconnect()
    print '''"r" is your handle to rserve. Type e.g. "r('1')" for string evaluation.'''
    r('x<-1:20; y<-x*2; lm(y~x)')
