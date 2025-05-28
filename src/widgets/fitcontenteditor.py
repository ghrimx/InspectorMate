from qtpy import (QtWidgets, Signal)

class FitContentTextEdit(QtWidgets.QTextEdit):
    """Plain Text Editor (QTextEdit subclass) that expand with the content
    
    Signal 'sigTextEdited' is emitted on 'focusOutEvent'
    """
    sigTextEdited = Signal(str)

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

    def focusOutEvent(self, e):
        if self._old_text != self.toPlainText():
            self.sigTextEdited.emit(self.toPlainText())
        return super().focusOutEvent(e)
    
    def focusInEvent(self, e):
        self._old_text = self.toPlainText()
        return super().focusInEvent(e)