import warnings
from version import __version__

# Show all deprecated warning only once:
warnings.filterwarnings('once', category=DeprecationWarning)
del warnings

from rconn import rconnect, connect
from taggedContainers import TaggedList


