from qtpy import (QtWidgets, Qt, QtGui, Slot)

from db.dbstructure import Signage
from signage.signagemodel import SignageTablelModel
from utilities import (utils, config as mconf)

from db.database import AppDatabase

from widgets.combobox import CheckableComboBox
from widgets.fitcontenteditor import FitContentTextEdit
from widgets.fileselectiondialog import selectFilesDialog


class CreateDialog(QtWidgets.QDialog):
    def __init__(self, model: SignageTablelModel, parent=None):
        super().__init__(parent=parent)

        self._model: SignageTablelModel = model
        self._relion_model = model.relationModel(model.Fields.Type.index)

        self.initUI()
        self.connect_signals()

    def initUI(self):
        self.setWindowTitle("Create Signage")

        form = QtWidgets.QFormLayout()

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.signage_type_combobox = QtWidgets.QComboBox()
        self.signage_type_combobox.setModel(self._relion_model)
        self.signage_type_combobox.setModelColumn(1)

        self.signage_prefix_lineedit = QtWidgets.QLineEdit()

        self.signage_refkey_lineedit = QtWidgets.QLineEdit()

        self.owner_editbutton = QtWidgets.QPushButton("...")
        self.owner_editbutton.clicked.connect(self.editOwner)
        self.owner_editbutton.setMaximumWidth(25)
        self.owner_combobox = QtWidgets.QComboBox()
        self.owner_combobox.setEditable(True)

        self.populateOwnerCombobox()

        owner_widget = QtWidgets.QWidget()
        owner_widget_layout = QtWidgets.QHBoxLayout()
        owner_widget.setLayout(owner_widget_layout)
        owner_widget_layout.addWidget(self.owner_combobox)
        owner_widget_layout.addWidget(self.owner_editbutton)
        owner_widget_layout.setContentsMargins(0, 0, 0, 0)

        self.signage_title_lineedit = FitContentTextEdit()
        self.signage_title_lineedit.setPlaceholderText("Enter text...")
        self.signage_title_lineedit.setMinimumWidth(500)

        self.signage_link_hiddenField = "InspectorMate:///Global"

        form.addRow("Type:", self.signage_type_combobox)
        form.addRow("Owner:", owner_widget)
        form.addRow("Prefix:", self.signage_prefix_lineedit)
        form.addRow("RefKey", self.signage_refkey_lineedit)
        form.addRow("Title", self.signage_title_lineedit)

        form.addWidget(self.buttonBox)
        self.setLayout(form)

        self.shortcut_save = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+S"), self, self.accept, context=Qt.ShortcutContext.WidgetWithChildrenShortcut)

    @Slot()
    def editOwner(self):
        dlg = OwnerDialog()
        dlg.exec()
        self.owner_combobox.clear()
        self.populateOwnerCombobox()

    def populateOwnerCombobox(self):
        self._owners: list = mconf.settings.value("owners", [], "QStringList")

        if self._owners is not None:
            for owner in self._owners:
                self.owner_combobox.addItem(owner)

    def setRefKey(self, last_refKey):
        new_refKey = utils.increment_refKey(last_refKey)
        self.signage_refkey_lineedit.setText(new_refKey)

    def connect_signals(self):
        self.signage_type_combobox.activated.connect(self.update_refKey_fields)
        self.signage_prefix_lineedit.textChanged.connect(self.update_refKey_fields)

    def update_refKey_fields(self):
        signage_type = self.signage_type_combobox.currentText()
        prefix = self.signage_prefix_lineedit.text()
        if prefix == "":
            prefix = "0"
        refKey = self._model.get_last_id(signage_type=signage_type, prefix=prefix)
        if refKey == "":
            refKey = f'{prefix}{0:03d}'
        self.setRefKey(refKey)

    def saveSignage(self):
        self.new_signage = Signage(note="",
                                   public_note="",
                                   status_id=1,
                                   owner=self.owner_combobox.currentText(),
                                   type_id=self.signage_type_combobox.currentIndex() + 1,
                                   refKey=self.signage_refkey_lineedit.text(),
                                   title=self.signage_title_lineedit.toPlainText(),
                                   creation_datetime="",
                                   modification_datetime="",
                                   link=self.signage_link_hiddenField,
                                   workspace_id=AppDatabase.active_workspace.id)

        res = self._model.insertSignage(self.new_signage)

        if res is not True:
            dlg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Critical, "Error saving signage", f"Signage: {self.new_signage}", QtWidgets.QMessageBox.StandardButton.Ok, self)
            dlg.exec()

    def getNewSignage(self):
        return self.new_signage
  
    def accept(self):
        self.saveSignage()
        super().accept()


class OwnerDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Add/Remove Owner")

        self.list_widget = QtWidgets.QListWidget()

        self._owners: list = mconf.settings.value("owners", [], "QStringList")

        if self._owners is not None:
            for owner in self._owners:
                list_item = QtWidgets.QListWidgetItem()
                list_item.setText(owner)
                self.list_widget.addItem(list_item)

        add_button = QtWidgets.QPushButton("Add")
        add_button.clicked.connect(self.addListItem)

        remove_button = QtWidgets.QPushButton("Remove")
        remove_button.clicked.connect(self.removeOneItem)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(add_button)
        hbox.addWidget(remove_button)

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        vbox.addWidget(self.list_widget)        
        vbox.addLayout(hbox)        

    def addListItem(self):
        """Add a single item to the list widget."""
        text, ok = QtWidgets.QInputDialog.getText(self, "New Item", "Add item:")
        if ok and text != "":
            list_item = QtWidgets.QListWidgetItem()
            list_item.setText(text)
            self.list_widget.addItem(list_item)
            self._owners.append(text)
            mconf.settings.setValue("owners", self._owners)

    def removeOneItem(self):
        """Remove a single item from the list widget."""
        row = self.list_widget.currentRow()
        item = self.list_widget.takeItem(row)
        self._owners.pop(row)
        mconf.settings.setValue("owners", self._owners)
        del item


class ExportDialog(QtWidgets.QDialog):
    def __init__(self, model: SignageTablelModel):
        super().__init__()

        self.setWindowTitle("Export Signage")

        self._model = model

        form = QtWidgets.QFormLayout(self)
        self.setLayout(form)

        filename_widget = QtWidgets.QWidget()
        filename_layout = QtWidgets.QHBoxLayout()
        filename_widget.setLayout(filename_layout)

        self.filename = QtWidgets.QLineEdit(self)
        self.filename.setText("output")
        self.filename.setMinimumWidth(500)
        self.filename.textChanged.connect(self.updateButtonState)

        filename_layout.addWidget(self.filename)
        filename_layout.addWidget(QtWidgets.QLabel(".xlsx"))
        filename_layout.setContentsMargins(0, 0, 0, 0)

        self.destination_button = QtWidgets.QPushButton("Destination")
        self.destination_button.clicked.connect(self.selectFolder)
        self.destination = QtWidgets.QLineEdit(self)
        self.destination.setText(AppDatabase.active_workspace.rootpath)
        self.destination.setReadOnly(True)

        self.signage_type = CheckableComboBox()
        self.signage_type.addItems(AppDatabase.cache_signage_type)
        self.signage_type.selectionChanged.connect(self.updateButtonState)

        self.include_public_note = QtWidgets.QCheckBox("Export Public Note", self)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        form.addRow("Type", self.signage_type)
        form.addRow("Filename", filename_widget)
        form.addRow(self.destination_button, self.destination)
        form.addRow("", self.include_public_note)
        form.addWidget(self.buttonBox)

        self.updateButtonState()

    def updateButtonState(self):
        if self.filename.text() != "" and self.destination != "" and len(self.signage_type.currentData()) > 0:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    @Slot()
    def selectFolder(self):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(caption='',
                                                                 directory=AppDatabase.active_workspace.rootpath,
                                                                 options=QtWidgets.QFileDialog.Option.ShowDirsOnly)
        if folder_path != "":
            self.destination.setText(folder_path)
            self.updateButtonState()

    def accept(self):
        err = self._model.export2Excel(self.signage_type.currentData(),
                                       f"{self.destination.text()}/{self.filename.text()}.xlsx",
                                       self.include_public_note.isChecked())

        if isinstance(err, PermissionError):
            QtWidgets.QMessageBox.critical(None,
                                           "Error writing the file to disk",
                                           f"PermissionError: {err.strerror}\nCheck the file is not opened",
                                           buttons=QtWidgets.QMessageBox.StandardButton.Ok)
        elif isinstance(err, OSError):
            QtWidgets.QMessageBox.critical(None,
                                           "Error writing the file to disk",
                                           f"{err.strerror}",
                                           buttons=QtWidgets.QMessageBox.StandardButton.Ok)
        else:
            super().accept()


class ImportDialog(QtWidgets.QDialog):
    def __init__(self, model: SignageTablelModel):
        super().__init__()

        self._model = model

        self._files = []

        form = QtWidgets.QFormLayout(self)
        self.setLayout(form)

        select_file_button = QtWidgets.QPushButton("Select Files")
        self.selected_file = QtWidgets.QLabel("0 files")
        select_file_button.clicked.connect(self.selectFiles)

        self.update_checkbox = QtWidgets.QCheckBox()
        self.update_checkbox.setCheckState(Qt.CheckState.Unchecked)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        form.addRow(select_file_button, self.selected_file)
        form.addRow("Update", self.update_checkbox)
        form.addWidget(self.buttonBox)

        self.updateButtonState()

    @Slot()
    def selectFiles(self):
        self._files = selectFilesDialog("*.xls*", AppDatabase.active_workspace.rootpath)
        self.selected_file.setText(f"{len(self._files)} files")
        self.updateButtonState()

    def updateButtonState(self):
        if len(self._files) > 0:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def accept(self):
        self._model.importFromFiles(self._files, self.update_checkbox.isChecked())
        super().accept()
