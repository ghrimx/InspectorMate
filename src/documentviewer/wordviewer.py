import logging
from mammoth import convert_to_html

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt, pyqtSlot as Slot

from documentviewer.viewerwidget import ViewerWidget
from qt_theme_manager import theme_icon_manager

logger = logging.getLogger(__name__)


class WordViewer(ViewerWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._document = None
        self.zoom_factor: int = 0
    
    @classmethod
    def viewerName(cls):
        return "WordViewer"
    
    @classmethod
    def supportedFormats(cls) -> list[str]:
        return [".docx"]

    def initViewer(self):
        self.left_pane.hide()
        self._toolbar.removeAction(self.fold_left_pane)
        self._toolbar.removeAction(self.action_first_separator)

        self.viewer = QtWidgets.QTextBrowser()
        self.viewer.setOpenExternalLinks(True)    
        self.viewer.setReadOnly(True) # enforce read-only
        self.viewer.setUndoRedoEnabled(False)
        self.viewer.setStyleSheet("QTextBrowser { background: #ffffff; }")
        self.viewer.document().setTextWidth(600)
        self.viewer.document().setDocumentMargin(60)
        self.viewer.setFixedWidth(900)

        self.scroll_area.setWidget(self.viewer)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ---Add Action---
        # Citation
        self.action_cite.triggered.connect(lambda: self.cite(self.citation()))
        self._toolbar.insertAction(self.toolbarFreeSpace(), self.action_cite)

        # Snipping tool
        self.capture_area.triggered.connect(lambda: self.capture(self.citation()))
        self._toolbar.insertAction(self.toolbarFreeSpace(), self.capture_area)

        # Create Signage
        self._toolbar.insertAction(self._toolbar_spacer, self.action_create_child_signage)

        self._toolbar.addSeparator()

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
        self.extension = filepath.split('.')[-1].lower()

        if not filepath.lower().endswith(".docx"):
            logger.error("Only .docx files are supported.")
            return
        
        custom_css = """
        <style>
            h1, h2, h3, h4, h5, h6 { 
                color: #0d6efd; 
            }
            .btn { 
                background-color: #198754; color: white; padding: .5rem 1rem; border-radius: .25rem; 
            }
            table, th, td {
                border: 1px solid black;
                padding: 5px;
            }
            table {
                border-collapse: collapse;
            }
        </style>
        """

        try:
            with open(filepath, "rb") as docx_file:
                result = convert_to_html(docx_file)
                html = result.value
                styled_html = custom_css + html
        except Exception as e:
            logger.error(self, "Fail to open", str(e))
            return 
        
        try:
            self.viewer.setHtml(styled_html)
            self.zoom_factor = 3
            self.viewer.zoomIn(self.zoom_factor)
        except Exception as e:
            logger.error(self, "Failed to render html", str(e))

    Slot()
    def citation(self) -> str:
        refkey =  "refkey: " + self.refKey.text() if self.refKey.text() != "" else None
        title = f'"{self.title.toPlainText()}"'
        citation = "; ".join(x for x in [refkey, title, self.subtitle.text(), self.reference.text(), self.extension] if x)
        return f"[{citation}]"
    
    def source(self) -> str:
        title = self._document.title
        source = f'{{"application":"InspectorMate", "module":"{self.viewerName()}", "item":"document", "item_title":"{title}"}}'
        return source
   


