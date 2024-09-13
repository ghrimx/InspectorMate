from qtpy import (Qt, QtWidgets)

class FitContentTextEdit(QtWidgets.QTextEdit):
    def __init__(self, readonly=False):
        super().__init__()
        self.setReadOnly(readonly)
        self.textChanged.connect(self.autoResize)

    def autoResize(self):
        self.document().setTextWidth(self.viewport().width())
        margins = self.contentsMargins()
        height = int(self.document().size().height() + margins.top() + margins.bottom())
        self.setFixedHeight(height)

    def resizeEvent(self, event):
        self.autoResize()