import logging
from qtpy import QtWidgets

from signage.connector_model import ConnectorModel, Connector, AppDatabase
from common import ConnectorType

from onenote.msonenote import OnenotePickerDialog
from qt_theme_manager import theme_icon_manager

logger = logging.getLogger(__name__)


class ConnectorManagerDialog(QtWidgets.QDialog):

    def __init__(self, model: ConnectorModel, parent=None):
        super().__init__(parent=parent)
        self._model = ConnectorModel() if model is None else model
        self.initUI()
        self.initConnection()

    def initUI(self):
        self.setWindowTitle('Connector Manager')
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        self.vlayout = QtWidgets.QVBoxLayout()

        button_layout = QtWidgets.QHBoxLayout()

        self.add_button = QtWidgets.QPushButton("Add Connector")
        self.add_button.setIcon(theme_icon_manager.get_icon(':add-box'))

        self.delete_button = QtWidgets.QPushButton("Delete Connector")
        self.delete_button.setIcon(theme_icon_manager.get_icon(':delete-bin2'))

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()

        self.edit_container = QtWidgets.QWidget()
        self.edit_container.setLayout(button_layout)

        self.table = QtWidgets.QTableView()
        self.table.setModel(self._model)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers) # ReadOnly
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

        for field in ConnectorModel.Fields.fields():
            if not field.visible:
                self.table.hideColumn(field.index)

        self.vlayout.addWidget(self.edit_container)
        self.vlayout.addWidget(self.table)
        self.setLayout(self.vlayout)

    def showEvent(self, a0):
        self.setMinimumWidth(600)
        return super().showEvent(a0)

    def initConnection(self):
        self.add_button.clicked.connect(self.onEditTriggered)
        self.delete_button.clicked.connect(self.removeConnector)
    
    def onEditTriggered(self):
        edit_dialog = ConnectorEditDialog(self)

        if edit_dialog.exec():
            ok = self._model.addConnector(edit_dialog.connector())

            if not ok:
                QtWidgets.QMessageBox.critical(self,
                                               "Connector Manager",
                                               "Failed to add connector")
                return
            self.table.resizeColumnsToContents()
            
    def removeConnector(self):
        index = self.table.selectionModel().currentIndex()

        if not index.isValid():
            return
        
        self._model.removeConnector(index)
        self.table.resizeColumnsToContents()


class ConnectorEditDialog(QtWidgets.QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._connector = Connector()
        self.setModal(False)
        self.initUI()
        self.connectSignals()

    def initUI(self):
        self.setWindowTitle("Connector Editor")
        form = QtWidgets.QFormLayout()
        self.setLayout(form)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.connector_type = QtWidgets.QComboBox()
        for connector_type in ConnectorType:
            self.connector_type.addItem(connector_type.value)
        self.source_btn = QtWidgets.QPushButton("Source")
        self.value_lineedit = QtWidgets.QLineEdit()

        self.value_lineedit.setReadOnly(True)
        self.value_lineedit.setPlaceholderText("Select the source")
        self.setMinimumWidth(500)

        form.addRow(QtWidgets.QLabel("Type"), self.connector_type)
        form.addRow(self.source_btn, self.value_lineedit)
        form.addWidget(self.buttonBox)

    def connectSignals(self):
        self.source_btn.clicked.connect(self.onSourceClicked)

    def setConnectorTypes(self, connectors: list):
        for type_id, name in connectors:
            self.connector_type.addItem(name, type_id)

    def showOneNoteDialog(self) -> str:
        onenote_manager = OnenotePickerDialog(self)
        onenote_manager.show()
        onenote_manager.connect()

        if not isinstance(onenote_manager, Exception):
            if onenote_manager.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                return onenote_manager.oeSection()
        else:
            QtWidgets.QMessageBox.critical(self,
                                           "Error",
                                            "",
                                            buttons=QtWidgets.QMessageBox.StandardButton.Ok)

    def onSourceClicked(self):
        source = None

        connector_type = self.connector_type.currentText()
        if connector_type == 'onenote':
            source = self.showOneNoteDialog()
        else:
           source, _ = QtWidgets.QFileDialog.getOpenFileName(caption="Select file",
                                                            directory=AppDatabase.activeWorkspace().rootpath,
                                                            filter=f"*.{connector_type}")
        if not source:
            return
        
        self.value_lineedit.setText(source)

    def connector(self) -> Connector:
        return self._connector

    def accept(self) -> None:
        self._connector.value = self.value_lineedit.text()
        self._connector.type = self.connector_type.currentText()
        super().accept()
