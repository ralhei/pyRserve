"""pyRserve package"""
import os
import sys
import warnings

from .rconn import connect
from .taggedContainers import TaggedList, TaggedArray, AttrArray

# Show all deprecated warning only once:
warnings.filterwarnings('once', category=DeprecationWarning)

if sys.version_info.major == 2:
    warnings.warn(
        'Python 2 is deprecated, it will no longer be supported in pyRserve 1.1',
        DeprecationWarning
    )
del warnings

__version__ = open(os.path.join(os.path.dirname(__file__),
                                'version.txt')).readline().strip()
