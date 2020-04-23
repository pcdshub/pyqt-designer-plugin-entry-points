import logging

from PyQt5 import QtWidgets

import pyqt_designer_plugin_entry_points

from . import conftest

logger = logging.getLogger(__name__)

WIDGET_KEY = pyqt_designer_plugin_entry_points.utils.ENTRYPOINT_WIDGET_KEY


def test_widgets(monkeypatch):
    class TestWidget(QtWidgets.QWidget):
        @classmethod
        def get_designer_info(cls):
            return dict(
                is_container=False,
                group='Group name',
                extensions=None,
                icon=None,
            )

    conftest.patch_entrypoint(
        monkeypatch, {WIDGET_KEY: dict(test_widget=TestWidget)}
    )

    widgets = pyqt_designer_plugin_entry_points.find_widgets()
    assert set(widgets) == {'test_widget'}
    assert widgets['test_widget']._info['cls'] is TestWidget


def test_smoke_no_designer_info(monkeypatch):
    class TestWidget(QtWidgets.QWidget):
        ...

    conftest.patch_entrypoint(
        monkeypatch, {WIDGET_KEY: dict(test_widget=TestWidget)}
    )

    assert set(pyqt_designer_plugin_entry_points.find_widgets()) == set()


def test_invalid_designer_info(monkeypatch):
    class TestWidget(QtWidgets.QWidget):
        @classmethod
        def get_designer_info(cls):
            return None

    conftest.patch_entrypoint(
        monkeypatch, {WIDGET_KEY: dict(test_widget=TestWidget)}
    )

    assert set(pyqt_designer_plugin_entry_points.find_widgets()) == set()
