from typing import Callable
from qtpy import (QtCore,
                  QtWidgets,
                  QtGui,
                  Slot)

from widgets.fitcontenteditor import FitContentTextEdit

from utilities import (utils, config as mconf)

from signage.signage_model import Signage, SignageType, SignageStatus

from widgets.combobox import CheckableComboBox


class CreateDialog(QtWidgets.QDialog):
    """QDialog to create various type of signage"""

    def __init__(self, signage_types: dict, getSignageLastRefkey: Callable, parent=None):
        super(CreateDialog, self).__init__(parent=parent)
        self._signage_types = signage_types
        self._getSignageLastRefkey = getSignageLastRefkey

        self.initUI()
        self.connectSignals()

    def initUI(self):
        self.setWindowTitle("Signage Dialog")

        form = QtWidgets.QFormLayout(self)
        self.setLayout(form)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.signage_type_combobox = QtWidgets.QComboBox()
        item: SignageType
        for key, item in self._signage_types.items():
            self.signage_type_combobox.insertItem(key, item.name)

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
        self.signage_title_lineedit.setAcceptRichText(False)
        self.signage_title_lineedit.setPlaceholderText("Enter text...")
        self.signage_title_lineedit.setMinimumWidth(500)
        
        form.addRow("Type:", self.signage_type_combobox)
        form.addRow("Owner:", owner_widget)
        form.addRow("Prefix:", self.signage_prefix_lineedit)
        form.addRow("Refkey", self.signage_refkey_lineedit)
        form.addRow("Title", self.signage_title_lineedit)

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, 
                                       QtWidgets.QSizePolicy.Policy.Expanding)
        
        form.addItem(spacer)
        form.addWidget(self.buttonBox)
        
        self.shortcut_save = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+S"),
                                             self,
                                             self.accept,
                                             context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)

    def connectSignals(self):
        self.signage_type_combobox.activated.connect(self.updateRefkeyField)
        self.signage_prefix_lineedit.textChanged.connect(self.updateRefkeyField)

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

    def setRefkey(self, last_refKey):
        new_refKey = utils.increment_refKey(last_refKey)
        self.signage_refkey_lineedit.setText(new_refKey)

    def updateRefkeyField(self):
        signage_type = self.signage_type_combobox.currentText()
        prefix = self.signage_prefix_lineedit.text()
        if prefix == "":
            p = r"^\d+"
        else:
            p = f"^{prefix}"
        refkey = self._getSignageLastRefkey(signage_type=signage_type, pattern=p)
        if refkey == "":
            refkey = f'{prefix}{0:03d}'
        self.setRefkey(refkey)

    def getNewSignage(self) -> Signage:
        """Return the new signage from the dialog"""
        new_signage = Signage(refkey=self.signage_refkey_lineedit.text(),
                              title=self.signage_title_lineedit.toPlainText(),
                              owner=self.owner_combobox.currentText(),
                              type=self.signage_type_combobox.currentIndex())
        return new_signage

    def accept(self):
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

    def showEvent(self, a0):
        self.adjustSize()
        return super().showEvent(a0)
    
class FilterDialog(QtWidgets.QDialog):
    def __init__(self, statuses: dict, signage_types: dict, parent=None):
        super().__init__(parent)
       
        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        form = QtWidgets.QFormLayout()
        self.setLayout(form)

        self.status_combobox = CheckableComboBox()
        for key, item in statuses.items():
            self.status_combobox.addItem(item.name, key)
        form.addRow("Status:", self.status_combobox)

        self.types_combobox = CheckableComboBox()
        for key, item in signage_types.items():
            self.types_combobox.addItem(item.name, key)
        form.addRow("Type:", self.types_combobox)

        _owners: list = mconf.settings.value("owners", [], "QStringList")
        self.owner_combobox = CheckableComboBox()
        self.owner_combobox.addItems(_owners)
        form.addRow("Owner:", self.owner_combobox)

        self.document_received = QtWidgets.QCheckBox("all", self)
        self.document_received.setCheckState(QtCore.Qt.CheckState.PartiallyChecked)
        self.document_received.checkStateChanged.connect(self.updateEvidenceCheckbox)
        form.addRow("Evidence:", self.document_received)

        form.addWidget(self.buttonBox)
    
    @Slot(QtCore.Qt.CheckState)
    def updateEvidenceCheckbox(self, state):
        if state == QtCore.Qt.CheckState.Unchecked:
            self.document_received.setText("without only")
        elif state == QtCore.Qt.CheckState.PartiallyChecked:
            self.document_received.setText("all")
        elif state == QtCore.Qt.CheckState.Checked:
            self.document_received.setText("with only")

    def resetFields(self):
        self.document_received.setCheckState(QtCore.Qt.CheckState.PartiallyChecked)
        self.status_combobox.clearSelection()
        self.types_combobox.clearSelection()
        self.owner_combobox.clearSelection()

    def accept(self):
        super().accept()

    def statusFilter(self):
        return [x for x in self.status_combobox.currentData()]

    def typeFilter(self):
        return [x for x in self.types_combobox.currentData()]     

    def ownerFilter(self):
        return [x for x in self.owner_combobox.currentData()]
    
    def evidenceFilter(self) -> QtCore.Qt.CheckState:
        return self.document_received.checkState()
    

class ExportDialog(QtWidgets.QDialog):
    def __init__(self, signage_types: dict, signage_statuses: dict, workspace_root: str = "", parent = None):
        super(ExportDialog, self).__init__(parent)
        self._workspace_root = workspace_root

        self.setWindowTitle("Export Signage")

        form = QtWidgets.QFormLayout(self)
        self.setLayout(form)

        # Output Filename
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

        # Destination button
        self.destination_button = QtWidgets.QPushButton("Destination")
        self.destination_button.clicked.connect(self.selectFolder)
        self.destination_lineedit = QtWidgets.QLineEdit(self)
        self.destination_lineedit.setText(self._workspace_root)
        self.destination_lineedit.setReadOnly(True)

        # Signage type
        self.type_combobox = CheckableComboBox()
        signage_type: SignageType
        for signage_type in signage_types.values():
            self.type_combobox.addItem(signage_type.name, signage_type)

        self.type_combobox.selectionChanged.connect(self.updateButtonState)

        # Signage statuses
        self.status_combobox = CheckableComboBox()
        signage_status: SignageStatus
        for signage_status in signage_statuses.values():
            self.status_combobox.addItem(signage_status.name, signage_status)

        # Public note
        self.public_note_checkbox = QtWidgets.QCheckBox("Export Public Note", self)

        # Standard buttons
        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # Forms
        form.addRow("Type", self.type_combobox)
        form.addRow("Status", self.status_combobox)
        form.addRow("Filename", filename_widget)
        form.addRow(self.destination_button, self.destination_lineedit)
        form.addRow("", self.public_note_checkbox)
        form.addWidget(self.buttonBox)

        self.updateButtonState()

    def updateButtonState(self):
        if self.filename.text() != "" and self.destination_lineedit != "" and len(self.type_combobox.currentData()) > 0:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    @Slot()
    def selectFolder(self):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(caption='',
                                                                 directory=self._workspace_root,
                                                                 options=QtWidgets.QFileDialog.Option.ShowDirsOnly)
        if folder_path != "":
            self.destination_lineedit.setText(folder_path)
            self.updateButtonState()

    def accept(self):
        self.selected_types = [value.uid for value in self.type_combobox.currentData()]
        self.selected_statuses = [value.uid for value in self.status_combobox.currentData()]
        self.outfile_destination = f"{self.destination_lineedit.text()}/{self.filename.text()}.xlsx"
        self.include_public_note = self.public_note_checkbox.isChecked()
        super().accept()


class ImportDialog(QtWidgets.QDialog):
    def __init__(self, workspace_root: str = "", parent = None):
        super(ImportDialog, self).__init__(parent)
        self._workspace_root = workspace_root
        self._files = []

        form = QtWidgets.QFormLayout(self)
        self.setLayout(form)

        select_file_button = QtWidgets.QPushButton("Select Files")
        self.selected_file = QtWidgets.QLabel("0 files")
        select_file_button.clicked.connect(self.selectFiles)

        self.update_checkbox = QtWidgets.QCheckBox()
        self.update_checkbox.setCheckState(QtCore.Qt.CheckState.Unchecked)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        form.addRow(select_file_button, self.selected_file)
        form.addRow("Update Title", self.update_checkbox)
        form.addWidget(self.buttonBox)

        self.updateButtonState()

    @Slot()
    def selectFiles(self):
        files = QtWidgets.QFileDialog.getOpenFileNames(caption="Select files", directory=self._workspace_root, filter="*.xls*")
        self._files = files[0]
        self.selected_file.setText(f"{len(self._files)} files")
        self.updateButtonState()

    def updateButtonState(self):
        if len(self._files) > 0:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def selectedFiles(self):
        return self._files

    def accept(self):
        self.update_title = self.update_checkbox.isChecked()
        super().accept()