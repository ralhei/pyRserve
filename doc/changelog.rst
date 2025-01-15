Changelog
=========
* V 1.1.0a2 (2025-01-15)
    * Include support for Python 3.9
* V 1.1.0a1 (2025-01-15)
    * Support for numpy2
    * Removed support for Python2
    * Switched from setup.py to pyproject.toml
    * Some variable naming cleanup (from camel-case to underscore-based)
* V 1.0.4 (2024-10-21)
    * Support connection to Rserve via sockets
    * Pin numpy to version below 2
* V 1.0.3 (2023-07-24)
    * Fixed setup.py to include requirements files
* V 1.0.2 (2023-01-01)
    * pytest checks for R in PATH
    * add list of required Linux (opensuse) packages for compiling R
* V 1.0.1 (2023-01-10)
    * Replace deprecated numpy.bool8 with numpy.bool_
    * Upgraded installation instructions in INSTALL file (more up-to-date R and Rserve)
    * Added Dockerfile for installing R and Rserve into container (used for github actions)
    * Enabled github actions for testing

* V 1.0.0 (2022-10-13)
    * Added docu for secure connection to Rserve via SSH tunnel
    * Updated meta data for pyRserve package
    * Added deprecation warning for Python 2
    * Corrected links to documentation

* V 1.0.0b3 (2021-06-25)
    Brought usage of pytest into the year 2021.

    * use fixtures for setting up an Rserve connection
    * put fixtures into conftest.py
    * added command line option for controlling rserve startup
    * properly named rserve-test.conf file.

* V 1.0.0b2 (2021-06-22)
    * Added missing version.txt file to wheel

* V 1.0.0b1 (2021-06-22)
    * Updated and cleanup documentation
    * Updated for more recent versions of R and Rserve
    * Added pre-commit hooks
    * Separated packages for dev/testing from production ones
    * Enhanced handling of NA values (thanks to Max Taggart)
    * Fixed numpy deprecation warnings (thanks to chaddcw)

* V 0.9.2 (2019-12-19)
    * Replaced deprecated numpy.fromstring with numpy.frombuffer
    * Flake8/pep8 cleanup
    * Refactored exception hierarchy
* V 0.9.1 (2017-05-19)
    * Removed a bug on some Python3 versions
    * Added proper support for S4 objects (`thanks to flying-sheep <https://github.com/flying-sheep>`_)
    * Added support for Python3 unitests on travis (`thanks to flying-sheep <https://github.com/flying-sheep>`_)

* V 0.9.0 (2016-04-11)
    * Full support for data objects larger than 2**24 bytes
    * Maximum size of message sent to Rserv can now be 2**64 bytes

* V 0.8.4 (2015-09-06)
    * fixed missing requirements.txt in MANIFEST.in
    * fixed bug in installer (setup.py)

* V 0.8.3 (2015-09-04)
    * Fixed exception catching for Python 3.4 (thanks to eeue56)
    * Some pep8 cleanups
    * explicit initialization of a number of instance variables in some classes
    * cleanup of import statements in test modules
    * Allow for message sizes greater than 4GB coming from R server

* V 0.8.2 (2015-07-11)
    * Added support for S4 objects (generated when e.g. creating a db object in R)

* V 0.8.1 (2014-07-17)
    * Fixed errors in the documentation, updated outdated parts
    * For unittesting run Rserve on different port from the default 6311 to
      avoid clashes with regular Rserve running on the same server
    * Fixed but when passing a R-function as argument to a function call (e.g. to ``sapply``),
      added unittest for this

* V 0.8.0 (2014-06-26)
    * Added support for remote shutdown of Rserve (thanks to Uwe Schmitt)
    * Added support for Out-Of-Bounds (OOB) messages (thanks to Philipp alias flying-sheep)

* V 0.7.3 (2013-08-01)
    * Added missing MANIFEST.in to produce a complete tgz package (now includes docs etc)
    * Fixed bug on x64 machines when handling integers larger than 2**31

* V 0.7.2 (2013-07-19)
    * Tested with Python 3.3.x, R 3.0.1 and Rserve 1.7.0
    * Updated documentation accordingly
    * Code cleanup for pep8 (mostly)
    * Marked code as production stable

* V 0.7.1 (2013-06-23)
    * Added link to new GitHub repository
    * fixed URL to documentation

* V 0.7.0 (2013-02-25)
    * Fixed problem when receiving very large result sets from R (added support for XT_LARGE header flag)
    * Correctly translate multi-dimensional R arrays into numpy arrays (preserve axes the right way)
      Removed 'arrayOrder' keyword argument as a consequence.
      THIS IS AN API CHANGE - PLEASE CHECK AND ADAPT YOUR CODE, ESPECIALLY IF YOU USE MULTI-DIM ARRAYS!!
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
