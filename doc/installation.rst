Installation
============

Before pyRserve can be used, R and Rserv have to be installed properly. 
Installation instructions for both packages are available on their corresponding
websites at `<http://www.r-project.org/>`_ and `<http://www.rforge.net/Rserve/>`_


Installing R from sources
-------------------------

For R being able to run Rserve properly it has to be installed with the
``--enable-R-shlib`` option.

The following command show how to do this for the sources. Make sure you have a
fortran compiler installed, otherwise installation will not be possible.

On Unix this looks like::

  tar -xzf R-3.0.1.tar.gz       # or whatever version you are using
  cd R-3.0.1
  ./configure --enable-R-shlib
  make
  make install

For Windows it might be just enough to install a prebuilt R package. The same
might be true for some Linux distributions, just make sure to install a
version which also contains all headers necessary for compiling Rserve in the
next step.

Installing Rserve
------------------

If you have already downloaded the tar file then from your command line run::

  R CMD INSTALL Rserve_1.7-0.tar.gz

Older versions of Rserve might also work, the earliest function version however
seems to be 0.6.6.

.. NOTE::
   Rserve usually daemonizes itself after starting from the command
   line. If you want to prevent this from happening (e.g. because you would
   like to control Rserve by a process management tool like ``supervisord``)
   then Rserve has to be install with the special ``-DNODAEMON`` compiler flag::

     PKG_CPPFLAGS=-DNODAEMON  R CMD INSTALL Rserve_1.7-0.tar.gz


Installing pyRserve
-------------------

For the following to work you have to have Python's ``setuptools``
(from `<http://pypi.python.org/pypi/setuptools>`_ ) to be installed.

pyRserve requires numpy to be installed (``easy_install numpy``).

Then from your unix/windows command line run::

  easy_install pyRserve

Note: pyRserve requires numpy. ``easy_install`` should install numpy
automatically if it's not there yet. However cases have been reported where
``easy_install`` fails doing this. The solution is to either install numpy
manually, or use `pip` instead of ``easy_install``. ``pip`` can be obtained
from `<http://pypi.python.org/pypi/pip>`_.

Currently supported Python versions are 2.7, 3.2, and 3.3.

In the next section you'll find instructions how to use everything together.
