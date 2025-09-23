from qtpy import (QtCore, Slot, Signal, QtWidgets)

from onenote.onenotemodel import OnenoteModel

from widgets.treeview import TreeView
from pyqtspinner import WaitingSpinner

from delegates.delegate import ReadOnlyDelegate 

class ConnectionThread(QtCore.QThread):
    sig_connected = Signal()

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent)

    def run(self, model: OnenoteModel):
        model.initConnection()
        model.refresh()
        self.sig_connected.emit()

class OnenotePickerDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.model = OnenoteModel()

        self.onenote_section = ""
        self.selected_item = None
        self.connection_thread: ConnectionThread = ConnectionThread(self)
        self.connection_thread.sig_connected.connect(self.handleConnectionEnded)
        
        self.initUI()       

    def connect2OneNote(self):
        self.waitingspinner = WaitingSpinner(self, True, True)
        self.waitingspinner.start()
        self.connection_thread.run(self.model)

    def handleConnectionEnded(self):
        self.connection_thread.quit()
        self.waitingspinner.stop()

    def initUI(self):
        self.setWindowTitle("OneNote Picker")
        vbox = QtWidgets.QVBoxLayout(self)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.onenote_tree = TreeView()
        self.onenote_tree.resizeColumnToContents(0)
        self.onenote_tree.setModel(self.model)

        vbox.addWidget(self.onenote_tree)
        vbox.addWidget(self.buttonBox)
        self.createDelegates()
        self.connectSignals()

    def show(self):
        super().show()
        self.connect2OneNote()

    def createDelegates(self):
        delegate = ReadOnlyDelegate(self)
        self.onenote_tree.setItemDelegate(delegate)

    def connectSignals(self):
        self.onenote_tree.selectionModel().selectionChanged.connect(self.onRowSelected)

    @Slot()
    def onRowSelected(self):
        selected_index = self.onenote_tree.selectionModel().currentIndex()
        self.selected_item = self.model.itemFromIndex(selected_index)

    def accept(self):
        if self.selected_item is not None:
            self.onenote_section = f'{{"section_name":"{self.selected_item.name}", "section_id":"{self.selected_item.id}"}}'
        super().accept()

    def oeSection(self):
        return self.onenote_section