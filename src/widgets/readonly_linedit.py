from qtpy import QtWidgets, QtCore

class ReadOnlyLineEdit(QtWidgets.QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setReadOnly(True)
        self.setStyleSheet("color: grey;")

    def event(self, event):
        # Prevent QDataWidgetMapper from trying to read user input
        if event.type() == QtCore.QEvent.Type.FocusOut:
            return True
        return super().event(event)