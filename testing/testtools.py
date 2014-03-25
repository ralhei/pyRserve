"""
Some helper functions for unit testing
"""
import subprocess
import time
import socket

from numpy import ndarray, float, float32, float64, complex, complex64, \
    complex128

# default port of R is 6311, but to avoid clashes with running Rserve
# instances use 6312 instead here for unittesting:
RSERVE_PORT = 6312


def start_pyRserve():
    """Setup connection to remote Rserve for unittesting"""
    # Start Rserve (in debug mode to ensure that it does not daemonize!!)
    rProc = subprocess.Popen(
        ['R', 'CMD', 'Rserve.dbg', '--no-save', '--RS-port', str(RSERVE_PORT)],
        stdout=open('/dev/null'), stderr=subprocess.PIPE)
    # wait a moment until Rserve starts listening on RSERVE_PORT
    time.sleep(0.6)
    if rProc.poll():
        # process has already terminated, so provide its output on stderr
        # to the user:
        raise RuntimeError('Rserve has terminated prematurely with the '
                           'following message: %s' % rProc.stderr.read())

    # store original socket timeout and set timeout to new value during startup
    # of Rserve:
    defaultTimeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(1)

    rserv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cnt = 0
    # give it a maximum of 10 tries with some sleep in between to wait for
    # Rserve to come into action!
    while cnt < 10:
        try:
            # open a socket connection to Rserve
            rserv.connect(('', RSERVE_PORT))
        except socket.error:
            time.sleep(0.3)
            cnt += 1
        else:
            # got a connection! Jump out of the loop
            break
    else:
        # after trying 10 times we still got no connection to Rserv - something
        # must be wrong.
        raise RuntimeError('Could not connect to Rserve')

    # set back original default timeout value:
    socket.setdefaulttimeout(defaultTimeout)

    # make a simple test that Rserve really answers correctly by looking at the
    # first few bytes:
    hdr = rserv.recv(1024)
    rserv.close()
    if not hdr.startswith(b'Rsrv01'):
        rProc.terminate()
        raise RuntimeError('received wrong header information from '
                           'socket (was: "%s")' % hdr[:10])
    return rProc


def compareArrays(arr1, arr2):
    """Helper function to compare two (possibly nested) numpy arrays"""
    def _compareArrays(arr1, arr2):
        assert arr1.shape == arr2.shape
        for idx in range(len(arr1)):
            if isinstance(arr1[idx], ndarray):
                _compareArrays(arr1[idx], arr2[idx])
            else:
                if type(arr1[idx]) in [float, float32, float64, complex,
                                       complex64, complex128]:
                    # make a comparison which works for floats and complex
                    # numbers
                    assert abs(arr1[idx] - arr2[idx]) < 0.000001
                else:
                    assert arr1[idx] == arr2[idx]
    try:
        _compareArrays(arr1, arr2)
    except TypeError:
        return False
    return True
