import os
from setuptools import setup
from pyRserve import __version__

PACKAGE_NAME = "pyRserve"

requirements = open('requirements.txt').read().splitlines()

# Get long_description from intro.txt:
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, 'doc', 'intro.rst')) as fp:
    long_description = fp.read()

setup(
    name=PACKAGE_NAME,
    version=__version__,
    description='A Python client to remotely access the R statistic package '
                'via network',
    long_description=long_description,
    author='Ralph Heinkel',
    author_email='rh@ralph-heinkel.com',
    url='https://pypi.org/project/pyRserve/',
    packages=['pyRserve'],
    install_requires=requirements,
    include_package_data=True,
    license='MIT license',
    platforms=['unix', 'linux', 'cygwin', 'win32'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Networking',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Mathematics',
    ],
)
