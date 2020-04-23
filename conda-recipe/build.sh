# Install the package
$PYTHON setup.py install --single-version-externally-managed --record=record.txt

DESIGNER_PLUGIN_PATH=$PREFIX/etc/pyqt-designer-plugin-entry-points
DESIGNER_PLUGIN_PATH_WIN="%CONDA_PREFIX%\etc\pyqt-designer-plugin-entry-points"

# Create auxiliary dirs
mkdir -p $PREFIX/etc/conda/activate.d
mkdir -p $PREFIX/etc/conda/deactivate.d
mkdir -p $DESIGNER_PLUGIN_PATH

# Create auxiliary vars
DESIGNER_PLUGIN=$DESIGNER_PLUGIN_PATH/designer_plugin.py
ACTIVATE=$PREFIX/etc/conda/activate.d/pyqt-designer-plugin-entry-points
DEACTIVATE=$PREFIX/etc/conda/deactivate.d/pyqt-designer-plugin-entry-points

# designer_plugin.py:
echo "from pyqt_designer_plugin_entry_points import *" >> $DESIGNER_PLUGIN

# SH activation script:
echo "export PYQTDESIGNERPATH=\$CONDA_PREFIX/etc/pyqt-designer-plugin-entry-points:\$PYQTDESIGNERPATH" >> $ACTIVATE.sh
echo "unset PYQTDESIGNERPATH" >> $DEACTIVATE.sh

# Windows activation script:
echo '@echo OFF' >> $ACTIVATE.bat
echo 'IF "%PYQTDESIGNERPATH%" == "" (' >> $ACTIVATE.bat
echo "  set PYQTDESIGNERPATH=${DESIGNER_PLUGIN_PATH_WIN}" >> $ACTIVATE.bat
echo ')ELSE (' >> $ACTIVATE.bat
echo "  set PYQTDESIGNERPATH=${DESIGNER_PLUGIN_PATH_WIN};%PYQTDESIGNERPATH%" >> $ACTIVATE.bat
echo ')' >> $ACTIVATE.bat

unset DESIGNER_PLUGIN_PATH
unset DESIGNER_PLUGIN_PATH_WIN
unset DESIGNER_PLUGIN
unset ACTIVATE
unset DEACTIVATE
