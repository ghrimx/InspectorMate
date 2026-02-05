import logging

from qtpy import (QtWidgets, QtCore, QtGui, Slot)

from documentviewer.viewerwidget import ViewerWidget
from qt_theme_manager import theme_icon_manager

logger = logging.getLogger(__name__)


class TxtViewer(ViewerWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._document = None
        self.zoom_factor: int = 0

    @classmethod
    def viewerName(cls):
        return "TxtViewer"
    
    @classmethod
    def supportedFormats(cls) -> list[str]:
        return [".txt", ".md", ".json"]
    
    def initViewer(self):
        self.left_pane.hide()
        self._toolbar.removeAction(self.fold_left_pane)
        self._toolbar.removeAction(self.action_first_separator)

        self.viewer = QtWidgets.QPlainTextEdit(self)
        self.viewer.setReadOnly(True)

        self.scroll_area.setBackgroundRole(QtGui.QPalette.ColorRole.Light)
        self.scroll_area.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.viewer)

        # --- Custom action ---

        # Zoom
        zoom_in = QtGui.QAction(theme_icon_manager.get_icon(":zoom-in"), "Zoom In", self)
        zoom_in.setShortcut(QtGui.QKeySequence.StandardKey.ZoomIn)
        zoom_in.triggered.connect(lambda: self.zoom(1))
        self._toolbar.insertAction(self.toolbarFreeSpace(), zoom_in)

        zoom_out = QtGui.QAction(theme_icon_manager.get_icon(":zoom-out"), "Zoom Out", self)
        zoom_out.setShortcut(QtGui.QKeySequence.StandardKey.ZoomOut)
        zoom_out.triggered.connect(lambda: self.zoom(-1))
        self._toolbar.insertAction(self.toolbarFreeSpace(), zoom_out)

        reset_zoom = QtGui.QAction(theme_icon_manager.get_icon(":find-replace-line"), "Reset Zoom", self)
        reset_zoom.setShortcut("Ctrl+0")
        reset_zoom.triggered.connect(self.resetZoom)
        self._toolbar.insertAction(self.toolbarFreeSpace(), reset_zoom)

    def zoom(self, f: int):
        if f > 0:
            self.viewer.zoomIn(1)
        elif f < 0:
            self.viewer.zoomOut(1)
        
        self.zoom_factor += f

    def resetZoom(self):
        while self.zoom_factor != 0:
            if self.zoom_factor > 0:
                self.viewer.zoomOut(1)
                self.zoom_factor -= 1
            if self.zoom_factor < 0:
                self.viewer.zoomIn(1)
                self.zoom_factor += 1

    def loadDocument(self, filepath: str = ""):
        if filepath == "":
            return
        
        self.extension = filepath.split('.')[-1]
        
        file = QtCore.QFile(filepath)
        try:
            file.open(QtCore.QIODevice.OpenModeFlag.ReadOnly | QtCore.QIODevice.OpenModeFlag.Text)
        except Exception as err:
            logger.error(err)
            return

        text_stream = QtCore.QTextStream(file)
        self.viewer.setPlainText(text_stream.readAll())
        self.zoom_factor = 3
        self.viewer.zoomIn(self.zoom_factor)

    def widget(self):
        return self.viewer

    Slot()
    def citation(self) -> str:
        refkey =  "refkey: " + self.refKey.text() if self.refKey.text() != "" else None
        title = f'"{self.title.toPlainText()}"'
        citation = "; ".join(x for x in [refkey, title, self.subtitle.text(), self.reference.text(), self.extension] if x)
        return f"[{citation}]"
    
    def getAnchor(self):
        return None
    
    def source(self) -> dict:
        title = self._document.title
        return {"application":"InspectorMate",
                "module":self.viewerName(),
                "item":"document",
                "item_title":title,
                "filepath":self._document.filepath.as_posix()}
