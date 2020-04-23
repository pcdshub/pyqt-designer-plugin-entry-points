from . import settings
from ._version import get_versions
from .core import (connect_events, enumerate_all_events,
                   enumerate_events_by_key, enumerate_events_by_signal_name,
                   enumerate_widgets)

__version__ = get_versions()['version']
del get_versions

__all__ = [
    'connect_events',
    'enumerate_all_events',
    'enumerate_events_by_key',
    'enumerate_events_by_signal_name',
    'enumerate_widgets',
    'settings',
]
