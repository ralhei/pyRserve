pyRserve
=========

What It Does
-------------

pyRerve is a library for connecting Python to an `R process <http://www.r-project.org/>`_
(an excellent statistic package) running `Rserve <http://www.rforge.net/Rserve/>`_ as a RPC connection gateway.
Through such a connection variables can be get and set in R from Python, and also R-functions can be called remotely.
In contrast to `rpy or rpy2 <http://rpy.sourceforge.net/>`_ the R process does not have to run on the same machine,
it can run on a remote machine and all variable  access and function calls will be delegated there through the network.

Furthermore - and this makes everything feel very pythonic - all data structures will automatically be converted
from native R to native Python and numpy types and back.

Why is pyRserve still 'beta'?
------------------------------------------------------

The question behind that usually is: Can pyRserve already be used for real work?

Well, pyRserve has been used at various companies in production mode for over two years now. So it is pretty stable
and many things work as they should.

However it is not complete yet - there are a few loose ends which should still be improved. Until then I still
consider it `beta`-status.

Changes
----------------
* V 0.7.0 (2013-02-25)
    * Fixed problem when receiving very large result sets from R (added support for XT_LARGE header flag)
    * Correctly translate multi-dimensional R arrays into numpy arrays (preserve axes the right way)
      Removed 'arrayOrder' keyword argument as a consequence. API CHANGE - PLEASE ADAPT YOUR CODE!
    * Support for conn.voidEval and conn.eval and new 'defaultVoid'-kw argument in the connect() function
    * Fixed bug in receiving multi-dimensional boolean (logical) arrays from R
    * Added support for multi-dimensional string arrays
    * added support for XT_VECTOR_EXPR type generated e.g. via "expression()" in R (will return a list
      with the expression content as list content)
    * windows users can now connect to localhost by pyRserve.connect() (omitting 'localhost' parameter)

* V 0.6.0 (2012-06-25)
    * support for Python3.x
    * Python versions <= 2.5 no more supported (due to Py3 support)
    * support for unicode strings in Python 2.x
    * full support complex numbers, partial support for 64bit integers and arrays
    * suport for Fortran-style ordering of numpy arrays
    * elements of single-item arrays are now translated to native python data types
    * much improved documentation
    * better unit test coverage
    * usage of the deprecated conn(<eval-string>) is no more possible
    * pyRserve.rconnect() now also removed

* V 0.5.2 (2011-12-02)
    * Fixed problem with 32bit integers being mistakenly rendered into 64bit integers on 64bit machines

* V 0.5.1 (2011-11-22)
    * Fixed improper DeprecationWarning when evaluating R statements via conn.r(...)

* V 0.5 (2011-10-03)
    * Renamed pyRserve.rconnect() to pyRserve.connect(). The former still works but shows a DeprecationWarning
    * String evaluation should now only be executed on the namespace directly, not on the connection object anymore.
      The latter still works but shows a DeprecationWarning.
    * New kw argument `atomicArray=True` added to pyRserve.connect() for preventing single valued arrays from being
      converted into atomic python data types.

* V 0.4 (2011-09-20)
    * Added support for nested function calls. E.g. conn.r.t.test( ....) now works.
    * Proper support for boolean variables and vectors

* V 0.3 (2010-06-08)
    * Added conversion of more complex R structures into Python
    * Updated documentation (installation, manual)
    
* V 0.2 (2010-03-19) Fixed rendering of TaggedArrays

* V 0.1 (2010-01-10) Initial version


Supported Platforms
----------------------------

This package has been mainly developed under Linux, and hence should run on all standard unix platforms, as well
 as on Mac OS X. pyRserve has also been successfully used on Win32 machines. Unittests have been used on the Linux
 and Mac OS X side, however they might just work fine for Win32.

It has been tested run with Python 2.6.x, 2.7.x and Python 3.2.

The latest development has been tested with R 2.13.1 and Rserve 0.6.6.

License
-------

pyRserve has been written by `Ralph Heinkel (www.ralph-heinkel.com) <http://www.ralph-heinkel.com/>`_ and is
released under `MIT license <http://packages.python.org/pyRserve/license.html>`_.


Quick Installation
-------------------
Make sure that Numpy is installed. Actually ``easy_install pyRserve`` should install numpy if it is missing.

Then from your unix/windows command line run::

    easy_install pyRserve
   
or download the tar.gz or zip package. After unpacking run ``python setup.py install`` from your command line.

Actually ``easy_install pyRserve`` should install numpy if it is missing. If it fails please use ``pip`` instead.

Documentation
----------------

Documentation can be found at `<http://packages.python.org/pyRserve/>`_.


Support
--------

For discussion of pyRserve issues and getting help please use the Google newsgroup
available at `<http://groups.google.com/group/pyrserve>`_.


Missing Features
-----------------
* Authentication is implemented in Rserve but not yet in pyRserve