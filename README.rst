Overview
=========

What pyRserve does
------------------

pyRserve is a library for connecting Python to `R  <http://www.r-project.org/>`_
(an excellent statistic package). Running `Rserve <http://www.rforge.net/Rserve/>`_
in R attaches the R-interpreter to a network socket, waiting for pyRserve to connect to it.
Through such a connection, variables can be get and set in R from Python,
and also R-functions can be called remotely.

In contrast to `rpy or rpy2 <http://rpy.sourceforge.net/>`_ the R process does not have to
run on the same machine, it can run on a remote machine and all variable  access and
function calls will be delegated there through the network.

Furthermore - and this makes everything feel very pythonic - all data structures will
automatically be converted from native R to native Python and numpy types and back.


Supported platforms
----------------------------

This package has been mainly developed under Linux, and hence should run on all standard unix
platforms, as well as on MacOS. pyRserve has also been successfully used on Windows machines.
Unittests have been used on the Linux and MacOS side, however they might just work fine for Windows.

It has been tested to work with Python 2.7.x, 3.6 to 3.9.

The latest development has been tested with some previous and current versions of R and Rserve.

License
-------
pyRserve has been written by Ralph Heinkel `(ralph-heinkel.com) <https://ralph-heinkel.com/>`_ and is
released under `MIT license <https://pyrserve.readthedocs.io/license>`_.


Quick installation
-------------------
From your unix/macOS,windows command line run::

    pip install pyRserve

For a fully functional setup also R and Rserve have to be installed. See section
`installation <https://pyrserve.readthedocs.io/installation>`_ in the pyRserve
documentation for instructions.


Quick usage
------------
Open a **first shell** and start up the R server, by calling the module `Rserve` that provides
the actual network connectivity for R::

    $ R CMD Rserve

R (Rserve) will now listen on port 6311 (on localhost). Of course Rserve can be configured to
listen on an exposed port and hence will be accessible from remote hosts as well.

Open a **second shell**, start Python, import pyRserve, and initialize the connection to Rserve::

    $ python
    >>> import pyRserve
    >>> conn = pyRserve.connect()

The default connection will be done on ``localhost:6311``. Other hosts can be reached by
calling ``pyRserve.connect(host=..., port=...)`` as well.


The ``conn`` object provides a namespace called ``conn.r`` that directly maps all variables
and other global symbols (like functions etc) and hence makes them accessible from Python.

Now create a vector in R, access the vector from Python (will be converted into a numpy array), and
call the ``sum()``-function in R::

    >>> conn.r("vec <- c(1, 2, 4)")
    >>> conn.r.vec                 # access vector 'vec' as an attribute of 'conn.r'
    array([1., 2., 4.])
    >>> conn.r.sum(conn.r.vec)     # 'sum' in running in the R-interpreter, returning the result to Python
    7.0

The other way around also works::

    >>> conn.r.somenumber = 444         # set a variable called 'somenumber' in the R interpreter...
    >>> conn.r("somenumber * 2")        # ... and double the number
    888.0


Source code repository
----------------------
pyRserve is now hosted on GitHub at `<https://github.com/ralhei/pyRserve>`_.


Documentation
----------------
Documentation can be found at `<https://pyrserve.readthedocs.io>`_.


Support
--------
For discussion of pyRserve and getting help please use the Google newsgroup
available at `<http://groups.google.com/group/pyrserve>`_.

Issues with the code (like bugs, etc.) should be reported on GitHub at
`<https://github.com/ralhei/pyRserve/issues>`_.


Missing features
-----------------
* Authentication is implemented in Rserve but not yet in pyRserve
* TLS encryption is not implemented yet in pyRserve. However using ssh tunnels
  can solve security issues in the meantime (see documentation).
