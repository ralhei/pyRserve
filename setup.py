#!/usr/bin/env python

import os
from distutils.core import setup


## Get long_description from intro.txt:
here = os.path.dirname(os.path.abspath(__file__))
f = open(os.path.join(here, 'doc', 'intro.rst'))
long_description = f.read()
f.close()

setup(name='pyRserve',
      version='0.3',     # ALWAYS UPDATE __version__  in __init__.py !!!
      description='A Python client to remotely access R statistic package via Rserve',
      long_description=long_description,
      author='Ralph Heinkel',
      author_email='rh [at] ralph-heinkel.com',
      url='http://pypi.python.org/pypi/pyRserve/',
      packages=['pyRserve'],
      license='MIT license',
      platforms=['unix', 'linux', 'cygwin', 'win32'],
      classifiers=[  'Development Status :: 3 - Alpha',
                     'Environment :: Console',
                     'License :: OSI Approved :: MIT License',
                     'Operating System :: POSIX',
                     'Operating System :: Microsoft :: Windows',
                     'Programming Language :: Python',
                     'Intended Audience :: Developers',
                     'Topic :: Scientific/Engineering :: Information Analysis',
                     'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
                     'Topic :: Scientific/Engineering :: Mathematics',
                     ],
     )
