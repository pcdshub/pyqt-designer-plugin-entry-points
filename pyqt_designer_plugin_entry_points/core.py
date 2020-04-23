import logging
import sys
import traceback

import entrypoints
from PyQt5 import QtCore, QtDesigner, QtGui

ENTRYPOINT_WIDGET_KEY = 'qt_designer_widgets'
ENTRYPOINT_EVENT_KEY = 'qt_designer_event'

logger = logging.getLogger(__name__)

_DESIGNER_HOOKS = None


def get_designer_hooks():
    global _DESIGNER_HOOKS
    if _DESIGNER_HOOKS is None:
        _DESIGNER_HOOKS = _DesignerHooks()
    return _DESIGNER_HOOKS


class _DesignerHooks(QtCore.QObject):
    """
    Class that handles the integration with the Qt Designer by hooking
    up slots to signals provided by FormEditor and other classes.
    """
    __instance = None

    formEditorSet = QtCore.pyqtSignal(QtCore.QObject)
    formWindowAdded = QtCore.pyqtSignal(QtCore.QObject)
    uncaughtExceptionRaised = QtCore.pyqtSignal(dict)

    def _get_hookable_signals(d):
        return tuple(attr for attr, obj in d.items()
                     if isinstance(obj, QtCore.pyqtSignal))

    hookable_signals = _get_hookable_signals(locals())

    def __init__(self):
        super().__init__()
        self._form_editor = None
        self._update_timer = None
        self._event_handlers = {}

    @property
    def form_editor(self):
        return self._form_editor

    @form_editor.setter
    def form_editor(self, editor):
        if self.form_editor is not None or not editor:
            return

        self._form_editor = editor
        self._setup_hooks()

        self.formEditorSet.emit(editor)

    def _setup_hooks(self):
        sys.excepthook = self._handle_exceptions

        manager = self.form_window_manager
        if manager:
            manager.formWindowAdded.connect(self.formWindowAdded.emit)

        if not self._update_timer:
            self._start_kicker()

    @property
    def form_window_manager(self):
        if not self.form_editor:
            return

        return self.form_editor.formWindowManager()

    @property
    def active_form(self):
        manager = self.form_window_manager
        if not manager:
            return

        return manager.activeFormWindow()

    def _update_widgets(self):
        widget = self.active_form
        if widget:
            widget.update()

    def _handle_exceptions(self, exc_type, value, trace):
        tb = ''.join(traceback.format_exception(exc_type, value, trace))
        print(f"""

Uncaught exception occurred while running Qt Designer:
------------------------------------------------------
{tb}
------------------------------------------------------
""", file=sys.stderr)
        self.uncaughtExceptionRaised.emit(
            dict(traceback=tb, exc_type=exc_type,
                 value=value, trace=trace)
        )

    def _start_kicker(self):
        self._update_timer = QtCore.QTimer()
        self._update_timer.setInterval(100)
        self._update_timer.timeout.connect(self._update_widgets)
        self._update_timer.start()


class DesignerPluginWrapper(QtDesigner.QPyDesignerCustomWidgetPlugin):
    """
    Parent class to standardize how plugins are accessed in qt designer.
    """

    _info = None

    def __init__(self):
        """
        Set up the plugin using the class info in cls
        """
        super().__init__()
        if self._info is None or not isinstance(self._info, dict):
            raise RuntimeError('DesignerPluginWrapper should be subclassed, '
                               'with _info set as a dictionary')

        self.initialized = False
        self.manager = None
        self._icon = self._info['icon'] or QtGui.QIcon()

    @classmethod
    def info(cls):
        """Information about the wrapped widget"""
        return dict(cls._info)

    def initialize(self, core):
        """
        Called to initialize the designer plugin

        Parameters
        ----------
        core : QtDesigner.QDesignerFormEditorInterface
            Form editor interface to use in the initialization
        """
        if self.initialized:
            return

        designer_hooks = get_designer_hooks()
        designer_hooks.form_editor = core

        if self._info['extensions']:
            self.manager = core.extensionManager()
            if self.manager:
                factory = ExtensionFactory(parent=self.manager)
                # Valid for Qt5:
                self.manager.registerExtensions(
                    factory, 'org.qt-project.Qt.Designer.TaskMenu'
                )
                # TODO: hooks?
        self.initialized = True

    def isInitialized(self):
        """
        Return True if initialize function has been called successfully.
        """
        return self.initialized

    @property
    def widget_class(self):
        """The widget class"""
        return self._info['cls']

    def createWidget(self, parent):
        """
        Instantiate a widget with the given parent.

        :param parent: Parent widget of instantiated widget
        :type parent:  QWidget
        """
        widget = self.widget_class(parent=parent)

        if hasattr(widget, 'init_for_designer'):
            # if inspect.signature() ... see if it will accept an info arg
            widget.init_for_designer(dict(self._info))

        return widget

    def name(self):
        """
        Return the class name of the widget.
        """
        return self.widget_class.__name__

    def group(self):
        """
        Group widgets by this name in the designer
        """
        return self._info['group']

    def toolTip(self):
        """
        A short description to pop up on mouseover.
        """
        return self._info['tooltip']

    def whatsThis(self):
        """
        A longer description of the widget for Qt Designer. By default, this
        is the entire class docstring.
        """
        return self._info.get('whatsthis', self.widget_class.__doc__ or '')

    def isContainer(self):
        """
        Return True if this widget can contain other widgets.
        """
        return self._info['is_container']

    def icon(self):
        """
        Return a QIcon to represent this widget in Qt Designer.
        """
        return self._icon

    def domXml(self):
        """
        XML Description of the widget's properties.
        """
        name = self.name()
        tooltip = self.toolTip()
        # TODO: hook here?
        return (f"""\
<widget class="{name}" name="{name}">
 <property name="toolTip" >
  <string>{tooltip}</string>
 </property>
</widget>
""")

    def includeFile(self):
        """
        Include the class module for the generated qt code
        """
        return self.widget_class.__module__

    @classmethod
    def from_class(cls, widget_cls, designer_info=None):
        assert not isinstance(cls, QtDesigner.QPyDesignerCustomWidgetPlugin)

        info = dict(
            cls=widget_cls,
            is_container=False,
            group='Designer Plugin Default',
            extensions=None,
            icon=None,
            tooltip='Designer plugin default tooltip',
        )

        try:
            if designer_info is None:
                designer_info = widget_cls.get_designer_info()
        except Exception as ex:
            raise ValueError(
                f'No designer info for widget for wrapping '
                f'{widget_cls.__name__}'
            ) from ex

        try:
            info.update(**designer_info)
        except Exception:
            raise ValueError(
                f'Invalid designer info for widget for wrapping '
                f'{widget_cls.__name__}: {designer_info}'
            ) from None

        return type(f'{cls.__name__}_WrappedDesignerPlugin',
                    (DesignerPluginWrapper, ),
                    dict(_info=info)
                    )


class ExtensionFactory(QtDesigner.QExtensionFactory):
    # def __init__(self, parent=None):
    #     super().__init__(parent=parent)

    def createExtension(self, obj, iid, parent):
        print('saw createExtension', obj, iid, parent)
        return None
        # if not isinstance(obj, PyDMPrimitiveWidget):
        #     return None

        # For now check the iid for TaskMenu...
        if iid == "org.qt-project.Qt.Designer.TaskMenu":
            ...
            # return PyDMTaskMenuExtension(obj, parent)

        # In the future we can expand to the others such as Property and etc
        # When the time comes...  we will need a new PyDMExtension and
        # the equivalent for PyDMTaskMenuExtension classes for the
        # property editor and an elif statement in here to instantiate it...
        return None


def enumerate_widgets():
    widgets = {}

    for entry in entrypoints.get_group_all(ENTRYPOINT_WIDGET_KEY):
        logger.info('Found widget: %s', entry.name)
        try:
            widget_cls = entry.load()
        except Exception:
            logger.exception("Failed to load %s entry: %s",
                             ENTRYPOINT_WIDGET_KEY, entry.name)
            continue

        if not isinstance(widget_cls,
                          QtDesigner.QPyDesignerCustomWidgetPlugin):
            try:
                widget_cls = DesignerPluginWrapper.from_class(widget_cls)
            except Exception as ex:
                logger.warning('Failed to add class %s: %s',
                               widget_cls, ex, exc_info=ex)
                continue

        widgets[entry.name] = widget_cls

    return widgets


def enumerate_events_by_key(key):
    for entry in entrypoints.get_group_all(key):
        try:
            target = entry.load()
        except Exception:
            logger.exception("Failed to load %s entry: %s",
                             key, entry.name)
            continue

        yield entry, target


def enumerate_events_by_signal_name(signal_name):
    yield from enumerate_events_by_key(f'{ENTRYPOINT_EVENT_KEY}.{signal_name}')


def enumerate_all_events():
    designer_hooks = get_designer_hooks()
    for signal_name in designer_hooks.hookable_signals:
        for event in enumerate_events_by_signal_name(signal_name):
            yield signal_name, event


def connect_events():
    designer_hooks = get_designer_hooks()
    results = {'discovered': {},
               'connected': {},
               }

    designer_hooks = get_designer_hooks()
    for signal_name, (entry, target) in enumerate_all_events():
        if signal_name not in results['discovered']:
            results['discovered'][signal_name] = 0
            results['connected'][signal_name] = 0

        results['discovered'][signal_name] += 1
        signal = getattr(designer_hooks, signal_name)
        try:
            signal.connect(target)
        except Exception:
            logger.exception("Failed to load %s entry: %s",
                             signal_name, entry.name)
            continue

        results['connected'][signal_name] += 1
        try:
            if not hasattr(target, '_entrypoint_signal_connected'):
                target._entrypoint_signal_connected = {}
            target._entrypoint_signal_connected[signal_name] = True
        except Exception:
            ...
            target._entrypoint_signal_connected = {}

    return results
