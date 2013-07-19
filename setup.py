#!/usr/bin/env python

import os
import sys
from distutils.core import setup

# NOTE: Other files to be included are specified in MANIFEST.in

## Get long_description from intro.txt:
here = os.path.dirname(os.path.abspath(__file__))
f = open(os.path.join(here, 'doc', 'intro.rst'))
long_description = f.read()
f.close()

sys.path.append('pyRserve')
from version import __version__

setup(name='pyRserve',
      version=__version__,
      description='A Python client to remotely access the R statistic package '
                  'via network',
      long_description=long_description,
      author='Ralph Heinkel',
      author_email='rh [at] ralph-heinkel.com',
      url='http://pypi.python.org/pypi/pyRserve/',
      packages=['pyRserve'],
      install_requires=['numpy'],
      license='MIT license',
      platforms=['unix', 'linux', 'cygwin', 'win32'],
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'License :: OSI Approved :: MIT License',
          'Operating System :: POSIX',
          'Operating System :: Microsoft :: Windows',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Intended Audience :: Developers',
          'Topic :: Software Development :: Libraries',
          'Topic :: System :: Networking',
          'Topic :: Scientific/Engineering :: Information Analysis',
          'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
          'Topic :: Scientific/Engineering :: Mathematics',
      ],
      )
