from setuptools import setup

setup(
    name='pyqt-designer-plugin-example',
    version='0.0.0',
    license='BSD',
    author='SLAC National Accelerator Laboratory',
    py_files='pyqt_designer_plugin_example',
    description='Entry point example',
    url='https://github.com/pcdshub/pyqt-designer-plugin-entry-points',
    entry_points={
        'qt_designer_widgets': [
            'MyWidget = pyqt_designer_plugin_example:MyWidget',
        ],
        'qt_designer_event.formWindowAdded': [
            'form_hook = pyqt_designer_plugin_example:form_added_hook',
        ]
    },
    install_requires=['pyqt-designer-plugin-entry-points'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
    ],
)
