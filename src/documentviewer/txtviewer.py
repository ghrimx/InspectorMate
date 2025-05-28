import logging

from qtpy import (QtWidgets, QtCore, QtGui, Slot)

from documentviewer.viewerwidget import ViewerWidget

from database.dbstructure import Document

logger = logging.getLogger(__name__)

class TxtViewer(ViewerWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._document = None

    @classmethod
    def viewerName(cls):
        return "TxtViewer"
    
    @classmethod
    def supportedFormats(cls) -> list[str]:
        return [".txt", ".md"]
    
    def initViewer(self):
        self._textreader = QtWidgets.QPlainTextEdit(self)
        self._textreader.setReadOnly(True)

        self.scroll_area.setBackgroundRole(QtGui.QPalette.ColorRole.Light)
        self.scroll_area.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self._textreader)

        # Citation
        self.action_cite = QtWidgets.QToolButton(self)
        self.action_cite.setIcon(QtGui.QIcon(":double-quotes"))
        self.action_cite.setShortcut(QtGui.QKeySequence("Ctrl+Alt+C"))
        self.action_cite.setToolTip("Copy citation (Ctrl+Alt+C)")
        self.action_cite.clicked.connect(lambda: self.cite(self.citation()))
        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.action_cite)

        # Snipping tool
        self.action_snip = QtWidgets.QToolButton(self)
        self.action_snip.setIcon(QtGui.QIcon(":capture_area"))
        self.action_snip.setShortcut(QtGui.QKeySequence("Ctrl+Alt+S"))
        self.action_snip.setToolTip("Capture Area (Ctrl+Alt+S)")
        self.action_snip.clicked.connect(lambda: self.capture(self.citation()))
        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.action_snip)

        # Create Signage
        self._toolbar.insertAction(self._toolbar_spacer, self.action_create_child_signage)

    def loadDocument(self, filepath: str = ""):
        if filepath == "":
            return
        
        file = QtCore.QFile(filepath)
        try:
            file.open(QtCore.QIODevice.OpenModeFlag.ReadOnly | QtCore.QIODevice.OpenModeFlag.Text)
        except Exception as err:
            logger.error(err)
            return

        text_stream = QtCore.QTextStream(file)
        self._textreader.setPlainText(text_stream.readAll())

    def widget(self):
        return self._textreader

    Slot()
    def citation(self) -> str:
        refkey =  "refkey: " + self.refKey.text() if self.refKey.text() != "" else None
        title = f'"{self.title.toPlainText()}"'
        citation = "; ".join(x for x in [refkey, title, self.subtitle.text(), self.reference.text()] if x)
        return f"[{citation}]"
    
    def source(self) -> str:
        title = self._document.title
        viewer = self.viewerName()
        source = f'{{"application":"InspectorMate", "module":"{viewer}", "item":"document", "item_title":"{title}"}}'
        return source
