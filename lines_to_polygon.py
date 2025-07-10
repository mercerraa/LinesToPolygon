from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsProject

# Import your processing logic here
from .polygon_from_lines import polygonise

class LinesToPolygon:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_action = None

    def initGui(self):
        self.plugin_action = QAction("Run Lines to polygon", self.iface.mainWindow())
        self.plugin_action.triggered.connect(self.run)
        self.iface.addPluginToMenu("&Lines to polygon", self.plugin_action)
        self.iface.addToolBarIcon(self.plugin_action)

    def unload(self):
        self.iface.removePluginMenu("&Lines to polygon", self.plugin_action)
        self.iface.removeToolBarIcon(self.plugin_action)

    def run(self):
        layer = self.iface.activeLayer()
        if not layer:
            QMessageBox.critical(None, "Error", "No active layer selected")
            return

        try:
            polygonise()

            QMessageBox.information(None, "Success", "Plugin executed successfully.")
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))
