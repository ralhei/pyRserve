#!/usr/bin/env python

from distutils.core import setup

setup(name='pyRserve',
      version='0.1',
      description='Python-to-Rserve connector',
      author='Ralph Heinkel',
      author_email='rh [at] ralph-heinkel.com',
      url='http://www.ralph-heinkel.com/pyRserve/',
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
