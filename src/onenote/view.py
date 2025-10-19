import logging
from qtpy import QtGui, QtCore, QtWidgets, Slot, Signal
from onenote import onenote_api as OE
from pyqtspinner import WaitingSpinner
from onenote.model import OnenoteModel, TreeStandardItem

logger = logging.getLogger(__name__)


class OnenotePickerDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.model = OnenoteModel()
        self.onenote_section: tuple = None
        self.selected_item = None

        self.setWindowTitle("OneNote Picker")
        self.setMinimumWidth(150)
        vbox = QtWidgets.QVBoxLayout(self)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.treeview = QtWidgets.QTreeView()
        self.treeview.resizeColumnToContents(0)
        self.treeview.setModel(self.model)
        
        self.treeview.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        vbox.addWidget(self.treeview)
        vbox.addWidget(self.buttonBox)
        self.spinner = WaitingSpinner(self.treeview)

        self.treeview.clicked.connect(self.onRowSelected)

    @Slot(QtCore.QModelIndex)
    def onRowSelected(self, index: QtCore.QModelIndex):
        self.selected_item: TreeStandardItem = self.model.itemFromIndex(index)

    def connect(self):
        self.model.clear()
        self.spinner.start()
        self.model.getHierarchy(self.spinner.stop, "", 4)

    def accept(self):
        if self.selected_item is not None:
            # self.onenote_section = f'{{"section_name":"{self.selected_item.name}", "section_id":"{self.selected_item.id}"}}'
            self.onenote_section = (self.selected_item.object_id, self.selected_item.name)
        super().accept()

