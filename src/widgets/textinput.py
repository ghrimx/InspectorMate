from qtpy import QtWidgets, Signal


class LineInput(QtWidgets.QLineEdit):
    """QLineEdit subclass

    Signal 'sigTextEdited' is emitted on 'focusOutEvent'
    """
    sigTextEdited = Signal(str)

    def __init__(self, parent = None):
        super(LineInput, self).__init__(parent)

    def focusOutEvent(self, e):
        """Emit signal if lose focus and text changed"""
        if self._old_text != self.text():
            self.sigTextEdited.emit(self.text())
        return super().focusOutEvent(e)
    
    def focusInEvent(self, e):
        self._old_text = self.text()
        return super().focusInEvent(e)