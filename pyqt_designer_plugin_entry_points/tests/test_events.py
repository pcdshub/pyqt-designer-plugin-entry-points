import logging

import pyqt_designer_plugin_entry_points

from . import conftest

logger = logging.getLogger(__name__)

EVENT_KEY = pyqt_designer_plugin_entry_points.utils.ENTRYPOINT_EVENT_KEY


def test_events(monkeypatch):
    def callable(arg):
        ...

    key = EVENT_KEY + '.formWindowAdded'

    conftest.patch_entrypoint(
        monkeypatch, {key: dict(callable=callable)}
    )

    results = pyqt_designer_plugin_entry_points.connect_events()
    print(results)
    assert results == {
        'discovered': {key: 1},
        'connected': {key: 1}
    }
    assert callable._entrypoint_signal_connected[key]
