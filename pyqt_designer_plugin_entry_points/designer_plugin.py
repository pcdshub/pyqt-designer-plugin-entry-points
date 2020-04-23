import pyqt_designer_plugin_entry_points

print("(pyqt_designer_plugin_entry_points hook)")

globals().update(**pyqt_designer_plugin_entry_points.enumerate_widgets())
