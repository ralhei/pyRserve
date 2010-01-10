pyRserve
=========

What It Does
-------------

pyRerve is a library for connecting Python to an `R process <http://www.r-project.org/>`_ (an excellent statistic package) 
running under `Rserve <http://www.rforge.net/Rserve/>`_. Through such a connection variables can be get and set in R from Python, 
and also R-functions can be called remotely.  In contrast to `rpy or rpy2 <http://rpy.sourceforge.net/>`_ the R process does not 
have to run on the same machine, it can run on a remote machine and all variable  access and function calls will be delegated there. 

Furthermore - and this makes everything feel very pythonic - all data structures will automatically be converted from native 
R to native Python types and back.

Supported Platforms
----------------------------

This package has been mainly developed under Linux, and hence should run on all standard unix platforms. It has also been
successfully used on Win32 machines. Unittests have only been used on the Linux side however they might just work 
fine for Win32.


License
-------

pyRserve has been written by `Ralph Heinkel (www.ralph-heinkel.com) <http://www.ralph-heinkel.com/>`_ and is released under `MIT license 
<http://packages.python.org/pyRserve/license.html>`_.


Quick Installation
-------------------

   easy_install pyRserve
   
or download the tar.gz or zip package below, and after unpacking run `python setup.py install` 
from your command line.


Full Documentation
------------------

Documentation can be found at `<http://packages.python.org/pyRserve/>`_.

