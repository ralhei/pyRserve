Installation
============

Before pyRserve can be used, R and Rserv have to be installed properly. 
Installation instructions for both packages are available on their corresponding
websites at`<http://www.r-project.org/>`_ and `<http://packages.python.org/pyRserve/>`_


Installing R from sources
-------------------------

For R being able to run Rserve properly it has to be installed with the `--enable-R-shlib` option.
On Unix this looks like::

  tar -xzf R-2.11.1.tar.gz       # or whatever version you are using
  cd R-2.11.1
  ./configure --enable-R-shlib
  make
  make install

For Windows it might be just enough to install a prepuilt R package. The same might be true for
some Linux distributions, just make sure to install a version which also contains all headers 
necessary for compiling Rserve in the next step.

Installing Rserve
------------------

If you have already downloaded the tar file then from your command line run::

  R CMD INSTALL Rserve_0.6-2.tar.gz


Installing PyRserve
-------------------

For the following to work you have to have Python's `setuptools` 
(from `<http://pypi.python.org/pypi/setuptools>`_ ) to be installed.

PyRserve requires numpy to be installed (`easy_install numpy`). 

Then from your unix/windows command line run::

  easy_install pyRserve


  
