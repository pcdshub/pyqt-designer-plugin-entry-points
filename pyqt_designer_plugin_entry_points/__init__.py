from ._version import get_versions
from .utils import connect_events, find_widgets

__version__ = get_versions()['version']
del get_versions

__all__ = ['find_widgets', 'connect_events']
