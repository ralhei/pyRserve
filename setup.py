#!/usr/bin/env python

import os
from distutils.core import setup

# NOTE: Other files to be included are specified in MANIFEST.in

## Get long_description from intro.txt:
here = os.path.dirname(os.path.abspath(__file__))
f = open(os.path.join(here, 'doc', 'intro.rst'))
long_description = f.read()
f.close()

setup(name='pyRserve',
      version='0.4',     # ALWAYS UPDATE __version__  in __init__.py and conf.py for sphinx!!!
      description='A Python client to remotely access R statistic package via Rserve',
      long_description=long_description,
      author='Ralph Heinkel',
      author_email='rh [at] ralph-heinkel.com',
      url='http://pypi.python.org/pypi/pyRserve/',
      packages=['pyRserve'],
      install_requires=['numpy'],
      license='MIT license',
      platforms=['unix', 'linux', 'cygwin', 'win32'],
      classifiers=[  'Development Status :: 4 - Beta',
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
