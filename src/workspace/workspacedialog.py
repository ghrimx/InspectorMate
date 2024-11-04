from qtpy import (QtCore, QtWidgets, QtGui, Signal, Slot)
from PyQt6.QtSql import QSqlRelationalDelegate

from workspace.workspacemodel import WorkspaceModel
from db.dbstructure import Workspace
from onenote.onenotepickerdlg import OnenotePickerDialog
from workspace.workspacetable import WorkspaceTable

from db.database import AppDatabase

from utilities.utils import createFolder


class WorkspaceManager(QtWidgets.QDialog):
    sig_workspace_updated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._model = WorkspaceModel()
        self.edit_dialog = None

        self.initUI()
        self.connectSignals()

    def initUI(self):
        self.setWindowTitle('Workspace Manager')
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        self.vlayout = QtWidgets.QVBoxLayout()

        button_layout = QtWidgets.QHBoxLayout()

        self.add_button = QtWidgets.QPushButton("Add Workspace")
        self.add_button.setIcon(QtGui.QIcon(':add-box'))

        self.edit_button = QtWidgets.QPushButton("Edit Workspace")
        self.edit_button.setIcon(QtGui.QIcon(':pencil'))

        self.delete_button = QtWidgets.QPushButton("Delete Workspace")
        self.delete_button.setIcon(QtGui.QIcon(':delete-bin2'))

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addStretch()

        self.edit_container = QtWidgets.QWidget()
        self.edit_container.setLayout(button_layout)

        self.workspace_table = WorkspaceTable(self._model)
        self.workspace_table.read_only()
        self.workspace_table.resizeColumnsToContents()
        self.workspace_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.workspace_table.hide_columns(self._model.hidden_fields())

        self.vlayout.addWidget(self.edit_container)
        self.vlayout.addWidget(self.workspace_table)
        self.setLayout(self.vlayout)

        self.adjust_size()

    def adjust_size(self):
        self.adjustSize()

        table_height = 0

        for r in range(self.workspace_table.verticalHeader().count()):
            table_height = table_height + self.workspace_table.rowHeight(r)

        margins = self.vlayout.contentsMargins()

        width = margins.left() + margins.right() + self.workspace_table.horizontalHeader().length() + self.workspace_table.verticalHeader().width() + self.workspace_table.frameWidth() * 2
        height = margins.top() + margins.bottom() + self.workspace_table.horizontalHeader().height() * 2 + table_height + self.edit_container.frameGeometry().height()

        self.resize(width, height)
        self.workspace_table.resizeColumnsToContents()

    def connectSignals(self):
        self.add_button.clicked.connect(self.addWorkspace)
        self.edit_button.clicked.connect(self.editWorkspace)
        self.delete_button.clicked.connect(self.deleteWorkspace)
        self.workspace_table.doubleClicked.connect(self.editWorkspace)

    @Slot()
    def addWorkspace(self):
        self.edit_dialog = None
        self.edit_dialog = WorkspaceEditDialog(model=self._model, model_index=QtCore.QModelIndex(), parent=self)
        if self.edit_dialog.exec():
            self.adjust_size()
            self.sig_workspace_updated.emit()

    @Slot()
    def editWorkspace(self):
        current_model_index = self.workspace_table.selectionModel().currentIndex()
        if self.edit_dialog is None:
            self.edit_dialog = WorkspaceEditDialog(model=self._model, model_index=current_model_index, parent=self)
        else:
            self.edit_dialog.mapper.setCurrentModelIndex(current_model_index)

        if self.edit_dialog.exec():
            self.adjust_size()
            self.sig_workspace_updated.emit()

    @Slot()
    def deleteWorkspace(self):
        row = self.workspace_table.selectionModel().currentIndex().row()
        res = self._model.deleteRow(row)
        if res:
            self._model.refresh()
            self.adjust_size()
            self.sig_workspace_updated.emit()


class WorkspaceEditDialog(QtWidgets.QDialog):
    def __init__(self, model: WorkspaceModel, model_index: QtCore.QModelIndex = QtCore.QModelIndex(), parent=None):
        super().__init__(parent=parent)

        self.model = model
        self.model_index = model_index

        self.initUI()
        self.connectSignals()
        self.setMapper()

    def initUI(self):
        self.setWindowTitle("Workspace Editor")

        form = QtWidgets.QFormLayout()

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.workspace_id_lineedit = QtWidgets.QLineEdit()
        self.workspace_name_lineedit = QtWidgets.QLineEdit()
        self.workspace_reference_lineedit = QtWidgets.QLineEdit()

        self.workspace_path_button = QtWidgets.QPushButton("Workspace")
        self.workspace_path_lineedit = QtWidgets.QLineEdit()
        self.workspace_path_lineedit.setReadOnly(True)
        self.workspace_path_lineedit.setPlaceholderText("Select the workspace folder")
        self.workspace_path_lineedit.setMinimumWidth(500)

        self.evidence_path_button = QtWidgets.QPushButton("Evidence")
        self.evidence_path_lineedit = QtWidgets.QLineEdit()
        self.evidence_path_lineedit.setReadOnly(True)
        self.evidence_path_lineedit.setPlaceholderText("Select the evidence folder")

        self.notebook_path_button = QtWidgets.QPushButton("Notebook")
        self.notebook_path_lineedit = QtWidgets.QLineEdit()
        self.notebook_path_lineedit.setReadOnly(True)
        self.notebook_path_lineedit.setPlaceholderText("Select the notebook folder")

        self.onenote_path_button = QtWidgets.QPushButton("OneNote")
        self.onenote_path_lineedit = QtWidgets.QLineEdit()
        self.onenote_path_lineedit.setReadOnly(True)
        self.onenote_path_lineedit.setPlaceholderText("Select the onenote section to monitor")

        self.activate_workspace = QtWidgets.QCheckBox("Activate workspace")
        self.activate_workspace.setChecked(True)

        form.addRow(QtWidgets.QLabel("Name"), self.workspace_name_lineedit)
        form.addRow(QtWidgets.QLabel("Reference"), self.workspace_reference_lineedit)
        form.addRow(self.workspace_path_button, self.workspace_path_lineedit)
        form.addRow(self.evidence_path_button, self.evidence_path_lineedit)
        form.addRow(self.notebook_path_button, self.notebook_path_lineedit)
        form.addRow(self.onenote_path_button, self.onenote_path_lineedit)
        form.addRow("", self.activate_workspace)
        form.addWidget(self.buttonBox)

        self.setLayout(form)
        self.updateButtonState()

        self.onenote_manager: OnenotePickerDialog = None

    def connectSignals(self):
        self.workspace_name_lineedit.textChanged.connect(self.updateButtonState)
        self.workspace_path_button.clicked.connect(lambda: self.selectFolder(self.workspace_path_lineedit))
        self.workspace_path_lineedit.textChanged.connect(self.onRootPathChanged)
        self.evidence_path_button.clicked.connect(lambda: self.selectFolder(self.evidence_path_lineedit))
        self.notebook_path_button.clicked.connect(lambda: self.selectFolder(self.notebook_path_lineedit))
        self.onenote_path_button.clicked.connect(self.onenoteButtonClicked)

    @Slot()
    def onenoteButtonClicked(self):
        if self.onenote_manager is None:
            self.onenote_manager = OnenotePickerDialog(self)

        self.onenote_manager.show()

        if not isinstance(self.onenote_manager, Exception):
            if self.onenote_manager.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                self.onenote_path_lineedit.setText(self.onenote_manager.oeSection())
        else:

            QtWidgets.QMessageBox.critical(self,
                                           "Error",
                                           "",
                                           buttons=QtWidgets.QMessageBox.StandardButton.Ok)

    @Slot()
    def onRootPathChanged(self):
        self.evidence_path_lineedit.setText(f"{self.workspace_path_lineedit.text()}/Evidence")
        self.notebook_path_lineedit.setText(f"{self.workspace_path_lineedit.text()}/Notebook")

    @Slot()
    def selectFolder(self, lineedit: QtWidgets.QLineEdit):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(caption='Select Folder',
                                                                 directory=AppDatabase.active_workspace.rootpath,
                                                                 options=QtWidgets.QFileDialog.Option.ShowDirsOnly)
        if folder_path != "":
            lineedit.setText(folder_path)
            self.updateButtonState()

    def updateButtonState(self):
        if self.workspace_name_lineedit.text() != "" and self.workspace_path_lineedit.text() != "":
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def setMapper(self):
        self.mapper = QtWidgets.QDataWidgetMapper(self)
        self.mapper.setItemDelegate(QSqlRelationalDelegate(self))
        self.mapper.setModel(self.model)
        self.mapper.setSubmitPolicy(QtWidgets.QDataWidgetMapper.SubmitPolicy.ManualSubmit)
        self.mapper.addMapping(self.workspace_id_lineedit, self.model.Fields.ID.index)
        self.mapper.addMapping(self.workspace_name_lineedit, self.model.Fields.Name.index)
        self.mapper.addMapping(self.workspace_reference_lineedit, self.model.Fields.Reference.index)
        self.mapper.addMapping(self.workspace_path_lineedit, self.model.Fields.Rootpath.index)
        self.mapper.addMapping(self.evidence_path_lineedit, self.model.Fields.EvidencePath.index)
        self.mapper.addMapping(self.notebook_path_lineedit, self.model.Fields.NotebookPath.index)
        self.mapper.addMapping(self.onenote_path_lineedit, self.model.Fields.OneNoteSection.index)
        self.mapper.addMapping(self.activate_workspace, self.model.Fields.State.index)
        self.mapper.setCurrentModelIndex(self.model_index)
        self.updateButtonState()

    def accept(self) -> None:
        workspace = Workspace()
        workspace.id = self.workspace_id_lineedit.text()
        workspace.name = self.workspace_name_lineedit.text()
        workspace.reference = self.workspace_reference_lineedit.text()
        workspace.rootpath = self.workspace_path_lineedit.text()
        workspace.state = self.activate_workspace.isChecked()
        workspace.onenote_section = self.onenote_path_lineedit.text()

        if self.evidence_path_lineedit.text() == "":
            workspace.evidence_path = self.workspace_path_lineedit.text()
        else:
            workspace.evidence_path = self.evidence_path_lineedit.text()
        if self.notebook_path_lineedit.text() == "":
            workspace.notebook_path = self.workspace_path_lineedit.text()
        else:
            workspace.notebook_path = self.notebook_path_lineedit.text()

        createFolder(workspace.evidence_path)
        createFolder(workspace.notebook_path)
        createFolder(f"{workspace.notebook_path}/.images")

        if self.mapper.currentIndex() < 0:
            self.model.insert(workspace)
        else:
            self.mapper.submit()
            self.model.refresh()

        super().accept()
