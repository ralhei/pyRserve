"""pyRserve package"""
import os
import warnings

from .rconn import connect
from .taggedContainers import TaggedList, TaggedArray, AttrArray

__version__ = open(os.path.join(os.path.dirname(__file__),
                                'version.txt')).readline().strip()

# Show all deprecated warning only once:
warnings.filterwarnings('once', category=DeprecationWarning)
del warnings
