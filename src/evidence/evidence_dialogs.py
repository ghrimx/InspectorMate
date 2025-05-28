from qtpy import QtWidgets
from widgets.combobox import CheckableComboBox

class FilterDialog(QtWidgets.QDialog):
    def __init__(self, statuses: dict, parent=None):
        super().__init__(parent)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        form = QtWidgets.QFormLayout()
        self.setLayout(form)

        self.status_combobox = CheckableComboBox()
        for item in statuses.values():
            self.status_combobox.addItem(item.name, item.name)

        form.addRow("Status:", self.status_combobox)
        form.addWidget(self.buttonBox)

    def accept(self):
        super().accept()

    def statusFilter(self):
        return [x for x in self.status_combobox.currentData()]
    
    def resetFields(self):
        self.status_combobox.clearSelection()
