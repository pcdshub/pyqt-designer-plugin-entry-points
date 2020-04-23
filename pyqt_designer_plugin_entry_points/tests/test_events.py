import logging

import pyqt_designer_plugin_entry_points

from . import conftest

logger = logging.getLogger(__name__)

EVENT_KEY = pyqt_designer_plugin_entry_points.core.ENTRYPOINT_EVENT_KEY


def test_events(monkeypatch):
    def callable(arg):
        ...

    signal_name = 'formWindowAdded'
    key = '.'.join((EVENT_KEY, signal_name))

    conftest.patch_entrypoint(
        monkeypatch, {key: dict(callable=callable)}
    )

    results = pyqt_designer_plugin_entry_points.connect_events()
    print(results)
    assert results['discovered'][signal_name] == 1
    assert results['connected'][signal_name] == 1
    assert callable._entrypoint_signal_connected[signal_name]
