import warnings

# Show all deprecated warning only once:
warnings.filterwarnings('once', category=DeprecationWarning)
del warnings

from rconn import rconnect, connect
from taggedContainers import TaggedList

__version__ = '0.5'

