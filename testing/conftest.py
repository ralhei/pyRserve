"""
Configurations and fixtures for testing pyRserve with pytest.
"""
import os
import time
import shutil
import socket
import subprocess

import pytest

import pyRserve.rexceptions

HERE_PATH = os.path.dirname(os.path.realpath(__file__))

# Use different port from default to avoid clashes with regular Rserve
# running on same machine:
EXTRA_RPORT = 6355


def start_Rserve(port):
    """Start an Rserve process for unittesting"""
    # First check that 'R' is in PATH:
    if not shutil.which('R'):
        pytest.exit("Cannot start R interpreter, R executable not in PATH", returncode=1)

    rProc = subprocess.Popen(
        ['R', 'CMD', 'Rserve', '--no-save', '--RS-conf',
         os.path.join(HERE_PATH, 'rserve-test.conf'),
         '--RS-port', str(port)],
        stdout=open('/dev/null'), stderr=subprocess.PIPE)
    # wait a moment until Rserve starts listening on EXTRA_RPORT
    time.sleep(0.6)
    if rProc.poll():
        # process has already terminated, so provide its stderr to the user:
        raise RuntimeError('Rserve has terminated prematurely with the '
                           'following message:  %s' % rProc.stderr.read())

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
            rserv.connect(('', port))
        except socket.error:
            time.sleep(0.3)
            cnt += 1
        else:
            # got a connection! Jump out of the loop
            break
    else:
        # after trying 10 times we still got no connection to Rserv - something
        # must be wrong.
        raise RuntimeError('Could not connect to Rserv over the network')

    # set back original default timeout value:
    socket.setdefaulttimeout(defaultTimeout)

    # make a simple test that Rserve really answers correctly by looking at the
    # first few bytes:
    hdr = rserv.recv(1024)
    rserv.close()
    if not hdr.startswith(b'Rsrv01'):
        rProc.terminate()
        raise RuntimeError(
            'received wrong header information from socket (was: "%s")'
            % str(hdr[:10])
        )
    return rProc


def pytest_addoption(parser):
    """Let the developer control whether or not to start extra Rserve process."""
    parser.addoption(
        "--run-rserve", action="store_true", default=False,
        help="Run separate Rserve process for unit testing on port %d" % EXTRA_RPORT
    )


@pytest.fixture(scope="session")
def run_rserve(request):
    """Fixture providing given command line option."""
    return request.config.getoption("--run-rserve")


@pytest.fixture(scope="module")
def conn(run_rserve):
    """Fixture providing a connection to a newly started Rserve process."""
    if run_rserve:
        # Fire up separate Rserve process:
        port = EXTRA_RPORT
        r_proc = start_Rserve(port)
    else:
        port = pyRserve.rconn.RSERVEPORT
        r_proc = None

    try:
        conn = pyRserve.connect(port=port)
    except pyRserve.rexceptions.RConnectionRefused:
        try:
            r_proc and r_proc.terminate()
        except subprocess.SubprocessError:
            pass
        pytest.exit('Error: Cannot reach running Rserve process.\nEither start'
                    'one manually or run pytest with option --run-rserve',
                    returncode=1)
        raise

    # Create an 'ident' function in R which just returns its argument.
    # Needed for testing below.
    conn.r('ident <- function(v) { v }')

    yield conn

    conn.close()
    r_proc and r_proc.terminate()
