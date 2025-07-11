from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsProject
from qgis.utils import iface

# Import your processing logic here
from .polygon_from_lines import polygonise

class LinesToPolygon:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_action = None

    def initGui(self):
        self.plugin_action = QAction("Lines to polygon", self.iface.mainWindow())
        #self.action = QAction(QIcon(os.path.join( os.path.dirname(__file__), 'icon.png' )), "Reverse layer order", self.iface.mainWindow())
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

            #QMessageBox.information(None, "Success", "Plugin executed successfully.")
            iface.messageBar().pushMessage("Success", "Lines to Polygon complete. Check for layers", level=Qgis.Success, duration=3)
        except Exception as e:
            #QMessageBox.critical(None, "Error", str(e))
            message = f'Error: {str(e)}'
            iface.messageBar().pushMessage("Warning", message, level=Qgis.Warning, duration=3)
