Installation
============

Before pyRserve can be used, R and Rserv have to be installed properly. 
Installation instructions for both packages are available on their corresponding
websites at `<http://www.r-project.org/>`_ and `<http://www.rforge.net/Rserve/>`_


Installing R from sources
-------------------------

For R being able to run Rserve properly it has to be installed with the `--enable-R-shlib` option.

The following command show how to do this for the sources. Make sure you have a
fortran compiler installed, otherwise installation will not be possible.

On Unix this looks like::

  tar -xzf R-2.13.1.tar.gz       # or whatever version you are using
  cd R-2.13.1
  ./configure --enable-R-shlib
  make
  make install

For Windows it might be just enough to install a prebuilt R package. The same might be true for
some Linux distributions, just make sure to install a version which also contains all headers 
necessary for compiling Rserve in the next step.

Installing Rserve
------------------

If you have already downloaded the tar file then from your command line run::

  R CMD INSTALL Rserve_0.6-6.tar.gz

Note that you have to run at least version 0.6.6 to get the unittests to work. Older versions of Rserve have a severe
implementation bug.

Installing PyRserve
-------------------

For the following to work you have to have Python's `setuptools` 
(from `<http://pypi.python.org/pypi/setuptools>`_ ) to be installed.

PyRserve requires numpy to be installed (`easy_install numpy`). 

Then from your unix/windows command line run::

  easy_install pyRserve

In the next section you'll find instructions how to use everything together.
  
