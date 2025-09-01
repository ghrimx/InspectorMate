import logging

# Related third party imports.
from qtpy import (QtCore, QtWidgets, QtGui, Signal, Slot)
from PyQt6.QtSql import QSqlRelationalDelegate

# Local application/library specific imports.
from workspace.workspacemodel import WorkspaceModel
from database.dbstructure import Workspace
# from onenote.onenotepickerdlg import OnenotePickerDialog
from onenote.msonenote import OnenotePickerDialog
from workspace.workspacetable import WorkspaceTable

from utilities.utils import createFolder

logger = logging.getLogger(__name__)


class WorkspaceManagerDialog(QtWidgets.QDialog):
    sigWorkspaceChanged = Signal()

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
        self.updateButtonState()

    def adjust_size(self):
        self.adjustSize()

        table_height = 0

        upper_bound = 10 if self.workspace_table.verticalHeader().count() > 10 else self.workspace_table.verticalHeader().count()
        for r in range(upper_bound):
            table_height = table_height + self.workspace_table.rowHeight(r)

        margins = self.vlayout.contentsMargins()

        width = margins.left() + margins.right() + self.workspace_table.horizontalHeader().length() + self.workspace_table.verticalHeader().width() + self.workspace_table.frameWidth() * 2
        height = margins.top() + margins.bottom() + self.workspace_table.horizontalHeader().height() * 2 + table_height + self.edit_container.frameGeometry().height()

        self.resize(width, height)

    def connectSignals(self):
        self.add_button.clicked.connect(lambda: self.openEditDialog(True))
        self.edit_button.clicked.connect(lambda: self.openEditDialog(False))
        self.delete_button.clicked.connect(self.deleteWorkspace)
        self.workspace_table.doubleClicked.connect(lambda: self.openEditDialog(False))
        self.workspace_table.clicked.connect(self.updateButtonState)
        
    def addWorkspace(self):
        workspace = Workspace()
        workspace.id = self.edit_dialog.workspace_id_lineedit.text()
        workspace.name = self.edit_dialog.workspace_name_lineedit.text()
        workspace.reference = self.edit_dialog.workspace_reference_lineedit.text()
        workspace.rootpath = self.edit_dialog.workspace_path_lineedit.text()
        workspace.state = self.edit_dialog.activate_workspace.isChecked()
        workspace.onenote_section = self.edit_dialog.onenote_path_lineedit.text()

        if self.edit_dialog.evidence_path_lineedit.text() == "":
            workspace.evidence_path = self.edit_dialog.workspace_path_lineedit.text()
        else:
            workspace.evidence_path = self.edit_dialog.evidence_path_lineedit.text()
        if self.edit_dialog.notebook_path_lineedit.text() == "":
            workspace.notebook_path = self.edit_dialog.workspace_path_lineedit.text()
        else:
            workspace.notebook_path = self.edit_dialog.notebook_path_lineedit.text()

        self.createChildFolder(workspace)

        ok, err = self._model.insertWorkspace(workspace)

        return ok, err
    
    def createChildFolder(self, workspace: Workspace):
        createFolder(workspace.evidence_path)
        createFolder(workspace.notebook_path)
        createFolder(f"{workspace.notebook_path}/.images")
        createFolder(f"{workspace.rootpath}/ListInsight")
            
    @Slot(bool)
    def openEditDialog(self, new: bool):
        current_model_index = self.workspace_table.selectionModel().currentIndex()

        if new:
            self.edit_dialog = None
            current_model_index = QtCore.QModelIndex()

        if self.edit_dialog is None:
            self.edit_dialog = WorkspaceEditDialog(self._model.activeWorkspace().rootpath, parent=self)
            self.edit_dialog.setMapper(self._model)
        
        self.edit_dialog.mapper.setCurrentModelIndex(current_model_index)
        self.edit_dialog.updateButtonState()

        if self.edit_dialog.exec():

            if new:
                ok, err = self.addWorkspace()
            else:
                self.edit_dialog.mapper.submit()
                ok = self._model.refresh()
                err = "Could not refresh workspace model"
                self.createChildFolder(self._model.activeWorkspace())

            if not ok:
                msg = QtWidgets.QMessageBox.critical(self,
                                                     "Workspace Manager",
                                                     err)
                return

            self.adjust_size()
            self.sigWorkspaceChanged.emit()

    @Slot()
    def deleteWorkspace(self): 
        index = self.workspace_table.selectionModel().currentIndex()
        parent = self.workspace_table.rootIndex()

        if not index.isValid():
            return
        
        if not self._model.removeRow(index.row(), parent):
            err = f"Cannot remove row from workspace model - Error: {self._model.lastError().text()}"
            logger.error(err)
            return 

        self._model.refresh()
        self.adjust_size()
        self.sigWorkspaceChanged.emit()

    def updateButtonState(self):
        index = self.workspace_table.selectionModel().currentIndex()
        
        if index.isValid():
            enable = True
        else:
            enable = False

        self.edit_button.setEnabled(enable)
        self.delete_button.setEnabled(enable)


class WorkspaceEditDialog(QtWidgets.QDialog):
    def __init__(self, workspace_rootpath: str = "", parent=None):
        super(WorkspaceEditDialog, self).__init__(parent=parent)
        self.workspace_rootpath = workspace_rootpath
        self.initUI()
        self.connectSignals()

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

        self.onenote_manager.model.refresh()
        self.onenote_manager.show()

        if not isinstance(self.onenote_manager, Exception):
            if self.onenote_manager.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                self.onenote_path_lineedit.setText(self.onenote_manager.oeSection())
        else:
            msg = QtWidgets.QMessageBox.critical(self,
                                                 "Error",
                                                 "",
                                                 buttons=QtWidgets.QMessageBox.StandardButton.Ok)
            msg.exec()

    @Slot()
    def onRootPathChanged(self):
        self.evidence_path_lineedit.setText(f"{self.workspace_path_lineedit.text()}/Evidence")
        self.notebook_path_lineedit.setText(f"{self.workspace_path_lineedit.text()}/Notebook")

    @Slot()
    def selectFolder(self, lineedit: QtWidgets.QLineEdit):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(caption='Select Folder',
                                                                 directory=self.workspace_rootpath,
                                                                 options=QtWidgets.QFileDialog.Option.ShowDirsOnly)
        if folder_path != "":
            lineedit.setText(folder_path)
            self.updateButtonState()

    def updateButtonState(self):
        if self.workspace_name_lineedit.text() != "" and self.workspace_path_lineedit.text() != "":
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def setMapper(self, model: WorkspaceModel):
        self.mapper = QtWidgets.QDataWidgetMapper(self)
        self.mapper.setItemDelegate(QSqlRelationalDelegate(self))
        self.mapper.setModel(model)
        self.mapper.setSubmitPolicy(QtWidgets.QDataWidgetMapper.SubmitPolicy.ManualSubmit)
        self.mapper.addMapping(self.workspace_id_lineedit, model.Fields.ID.index)
        self.mapper.addMapping(self.workspace_name_lineedit, model.Fields.Name.index)
        self.mapper.addMapping(self.workspace_reference_lineedit, model.Fields.Reference.index)
        self.mapper.addMapping(self.workspace_path_lineedit, model.Fields.Rootpath.index)
        self.mapper.addMapping(self.evidence_path_lineedit, model.Fields.EvidencePath.index)
        self.mapper.addMapping(self.notebook_path_lineedit, model.Fields.NotebookPath.index)
        self.mapper.addMapping(self.onenote_path_lineedit, model.Fields.OneNoteSection.index)
        self.mapper.addMapping(self.activate_workspace, model.Fields.State.index)

        self.updateButtonState()

    def accept(self) -> None:
        super().accept()
