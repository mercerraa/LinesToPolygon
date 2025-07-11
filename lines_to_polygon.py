from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.core import (
    Qgis
)
from qgis.utils import iface

import os

# Import your processing logic here
from .polygon_from_lines import polygonise

class LinesToPolygon:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.toolbar = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        self.action = QAction(QIcon(icon_path), "Lines to polygon", self.iface.mainWindow())
        self.action.triggered.connect(self.run)

        self.iface.addPluginToMenu("&Lines to polygon", self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removePluginMenu("&Lines to polygon", self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        layer = self.iface.activeLayer()
        if not layer:
            QMessageBox.critical(None, "Error", "No active layer selected")
            return

        try:
            polygonise()
            iface.messageBar().pushMessage("Success", "Lines to Polygon complete. Check for layers", level=Qgis.Success, duration=3)
        except Exception as e:
            message = f'Error: {str(e)}'
            iface.messageBar().pushMessage("Warning", message, level=Qgis.Warning, duration=3)
