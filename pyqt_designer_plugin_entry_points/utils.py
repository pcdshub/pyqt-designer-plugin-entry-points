import logging
import sys
import traceback

import entrypoints

from PyQt5 import QtGui, QtDesigner, QtCore, QtWidgets

# from .utilities import stylesheet

ENTRYPOINT_WIDGET_KEY = 'qt_designer_widgets'

logger = logging.getLogger(__name__)

_DESIGNER_HOOKS = None


def get_designer_hooks():
    global _DESIGNER_HOOKS
    if _DESIGNER_HOOKS is None:
        _DESIGNER_HOOKS = _DesignerHooks()
    return _DESIGNER_HOOKS


class _DesignerHooks(QtCore.QObject):
    """
    Class that handles the integration with PyDM and the Qt Designer by hooking
    up slots to signals provided by FormEditor and other classes.
    """
    __instance = None
    formWindowAdded = QtCore.pyqtSignal(QtCore.QObject)

    def __init__(self):
        super().__init__()
        self._form_editor = None
        self._update_timer = None

    @property
    def form_editor(self):
        return self._form_editor

    @form_editor.setter
    def form_editor(self, editor):
        if self.form_editor is not None:
            return

        if not editor:
            return

        self._form_editor = editor
        self._setup_hooks()

    def _setup_hooks(self):
        sys.excepthook = self._handle_exceptions

        manager = self.form_window_manager
        if manager:
            manager.formWindowAdded.connect(self.formWindowAdded.emit)
            manager.formWindowAdded.connect(
                self._new_form_added
            )

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

    def _new_form_added(self, form_window_interface):
        style_data = stylesheet._get_style_data(None)
        widget = form_window_interface.formContainer()
        widget.setStyleSheet(style_data)
        if not self._update_timer:
            self._start_kicker()

    def _update_widgets(self):
        widget = self.active_form
        if widget:
            widget.update()

    def _handle_exceptions(self, exc_type, value, trace):
        print("Exception occurred while running Qt Designer.")
        print(''.join(traceback.format_exception(exc_type, value, trace)))

    def _start_kicker(self):
        self._update_timer = QtCore.QTimer()
        self._update_timer.setInterval(100)
        self._update_timer.timeout.connect(self._update_widgets)
        self._update_timer.start()


class DesignerPluginWrapper(QtDesigner.QPyDesignerCustomWidgetPlugin):
    """
    Parent class to standardize how pydm plugins are accessed in qt designer.
    All functions have default returns that can be overriden as necessary.
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

    def initialize(self, core):
        """
        Override this function if you need special initialization instructions.
        Make sure you don't neglect to set the self.initialized flag to True
        after a successful initialization.

        Parameters
        ----------
        core : QtDesigner.QDesignerFormEditorInterface
            Form editor interface to use in the initialization
        """
        if self.initialized:
            return

        designer_hooks = _DesignerHooks()
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
        Return a common group name so all PyDM Widgets are together in
        Qt Designer.
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
        class Plugin(DesignerPluginWrapper):
            __doc__ = f"Designer plugin for {widget_cls.__name__}"

            def __init__(self):
                super().__init__(widget_cls, is_container, group, extensions, icon)

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
        except Exception:
            logger.debug('No designer info for widget for wrapping %s',
                         widget_cls.__name__)
            return None

        try:
            info.update(**designer_info)
        except Exception:
            logger.debug('Invalid designer info for wrapping %s: %s',
                         widget_cls.__name__, designer_info)
            return None

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


def find_widgets():
    widgets = {}

    for entry in entrypoints.get_group_all(ENTRYPOINT_WIDGET_KEY):
        logger.info('Found widget: %s', entry.name)
        try:
            widget_cls = entry.load()
        except Exception:
            logger.exception("Failed to load happi.containers entry: %s",
                             entry.name)
            continue

        if not isinstance(widget_cls, QtDesigner.QPyDesignerCustomWidgetPlugin):
            widget_cls = DesignerPluginWrapper.from_class(widget_cls)

        widgets[entry.name] = widget_cls

    widgets['test'] = DesignerPluginWrapper.from_class(TestWidget)
    return widgets


class TestWidget(QtWidgets.QWidget):
    @classmethod
    def get_designer_info(cls):
        return dict(
            is_container=False,
            group='Group name',
            extensions=None,
            icon=None,
        )
