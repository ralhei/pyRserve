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

.. NOTE::
    You need a couple of LINUX packages and libraries to be installed, like a fortran
    compile and readline/bzip2/... development libraries. On OpenSuse these can be installed
    with ``zypper install -y gcc-fortran readline-devel libbz2-devel xz-devel pcre2-devel libcurl-devel``
    Other Linux distributions provide packages with similar names.

On installing R then looks like::

  R_VER=4.4.1   # possibly find the latest version, or use the version you require
  curl -LO https://cran.r-project.org/src/base/R-4/R-${R_VER}.tar.gz
  tar -xzf R-${R_VER}.tar.gz
  cd R-${R_VER}
  ./configure --enable-R-shlib --disable-java -with-x=no
  make
  make install

For Windows it might be just enough to install a prebuilt R package. The same
might be true for some Linux distributions, just make sure to install a
version which also contains all headers necessary for compiling Rserve in the
next step.

Installing Rserve
------------------

If you have already downloaded the tar file then from your command line run::

  curl -LO http://www.rforge.net/Rserve/snapshot/Rserve_1.8-15.tar.gz
  R CMD INSTALL Rserve_1.8-15.tar.gz

Older versions of Rserve might also work, the earliest function version however
seems to be 0.6.6.

.. NOTE::
   Rserve usually daemonizes itself after starting from the command
   line. If you want to prevent this from happening (e.g. because you would
   like to control Rserve by a process management tool like ``supervisord``
   or want to control Rserve running the unittests with ``pytest --run-rserve``)
   then Rserve has to be install with the special ``-DNODAEMON`` compiler flag::

     PKG_CPPFLAGS=-DNODAEMON  R CMD INSTALL Rserve_1.8-12.tar.gz


Installing pyRserve
-------------------

From your unix/windows command line run::

  pip install pyRserve

If you want to develop or test locally, then also install extra packages for testing::

    pip install pyRserve[testing]

Currently supported Python versions are 3.6 to 3.11. It might still run on Python 2.7
but this is not supported anymore and will be deprecated in future versions.

In the next section you'll find instructions how to use everything together.


Running unittests
-----------------
After installation is completed - and for those who want to contribute to pyRserve's developement -
unittests can be run straight from the command line. Remember to have pyRserve installed with
the testing dependencies, as described in the previous section.

In the current setup pytest is able to automatically fire up an Rserve-process which needs to be available
for the unittests to run against. This is achieved by calling::

    $ pytest testing --run-rserve
    =========================== test session starts ===========================
    platform linux -- Python 3.11.3, pytest-7.4.0, pluggy-1.2.0
    rootdir: /home/user/pyRserve
    collected 50 items

    testing/test_rparser.py ..........................................                                                [ 84%]
    testing/test_taggedContainers.py ........                                                                         [100%]
    =========================== 50 passed in 4.19s ============================

In case you have Rserve already running on localhost, it is sufficient to call ``pytest testing``.
