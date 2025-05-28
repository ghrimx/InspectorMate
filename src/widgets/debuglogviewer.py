from qtpy import QtCore, QtWidgets
from pathlib import Path
from utilities import config as mconf


class DebugLogViewer(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(DebugLogViewer, self).__init__(parent)
        self.setWindowTitle("Debug Output")

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self._textreader = QtWidgets.QPlainTextEdit(self)
        self._textreader.setReadOnly(True)
        layout.addWidget(self._textreader)

        self.loadDocument(mconf.config.log_path)

        self._textreader.verticalScrollBar().setValue(self._textreader.verticalScrollBar().maximum())


    def loadDocument(self, filepath: Path):
        if not filepath.exists():
            return
        
        file = QtCore.QFile(filepath.as_posix())
        try:
            file.open(QtCore.QIODevice.OpenModeFlag.ReadOnly | QtCore.QIODevice.OpenModeFlag.Text)
        except Exception as err:
            # logger.error(err)
            return

        text_stream = QtCore.QTextStream(file)
        self._textreader.setPlainText(text_stream.readAll())