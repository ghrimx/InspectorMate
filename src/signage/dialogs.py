from datetime import date

from my_pyqt_widgets import FitContentTextEdit, MultiCheckableComboBox, DatePickerWidget
from qt_theme_manager import theme_icon_manager

from common import Signage, SignageStatus, SignageType, SignageExportParam
from database.database import AppDatabase
from qtpy import QtCore, QtGui, QtWidgets, Slot
from utilities.settings import get_settings
from utilities.utils import increment_refKey


class SignageDialog(QtWidgets.QDialog):
    """QDialog to create various type of signage"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle("Signage Dialog")

        form = QtWidgets.QFormLayout(self)
        self.setLayout(form)

        buttons = (
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.signage_type_combobox = QtWidgets.QComboBox()
        item: SignageType
        for key, item in AppDatabase.cache_signage_type.items():
            self.signage_type_combobox.insertItem(key, item.name)

        self.due_date_edit = DatePickerWidget()

        self.signage_prefix_lineedit = QtWidgets.QLineEdit()

        self.signage_refkey_lineedit = QtWidgets.QLineEdit()

        self.owner_editbutton = QtWidgets.QPushButton()
        self.owner_editbutton.setIcon(theme_icon_manager.get_icon(":user-line"))
        self.owner_editbutton.clicked.connect(self.editOwner)
        self.owner_editbutton.setMaximumWidth(25)
        self.owner_combobox = QtWidgets.QComboBox()
        self.owner_combobox.setEditable(True)

        self.populateOwnerCombobox()

        owner_widget_row = QtWidgets.QHBoxLayout()
        owner_widget_row.addWidget(self.owner_combobox, stretch=1)
        owner_widget_row.addWidget(self.owner_editbutton)

        self.signage_title_lineedit = FitContentTextEdit()
        self.signage_title_lineedit.setAcceptRichText(False)
        self.signage_title_lineedit.setPlaceholderText("Enter text...")
        self.signage_title_lineedit.setMinimumWidth(500)

        # --- Parent Signage ---
        self.parent_signage_id = QtWidgets.QLabel()
        self.parent_signage_id.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.parent_signage_refkey = QtWidgets.QLabel()
        self.parent_signage_refkey.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        hbox = QtWidgets.QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        self.parent_signage_widget = QtWidgets.QWidget()
        self.parent_signage_widget.setLayout(hbox)
        hbox.addWidget(QtWidgets.QLabel("Parent Refkey:"))
        hbox.addWidget(self.parent_signage_refkey)
        hbox.addWidget(QtWidgets.QLabel("Parent ID:"))
        hbox.addWidget(self.parent_signage_id)

        # --- Layout ---
        form.addWidget(self.parent_signage_widget)
        form.addRow("Type:", self.signage_type_combobox)
        form.addRow("Due date:", self.due_date_edit)
        form.addRow("Owner:", owner_widget_row)
        form.addRow("Prefix:", self.signage_prefix_lineedit)
        form.addRow("Refkey", self.signage_refkey_lineedit)
        form.addRow("Title", self.signage_title_lineedit)

        spacer = QtWidgets.QSpacerItem(
            20,
            40,
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )

        form.addItem(spacer)
        form.addWidget(self.buttonBox)

        self.shortcut_save = QtGui.QShortcut(
            QtGui.QKeySequence("Ctrl+S"),
            self,
            self.accept,
            context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut,
        )

        # Connections
        self.signage_type_combobox.activated.connect(self.updateRefkeyField)
        self.signage_prefix_lineedit.textChanged.connect(self.updateRefkeyField)

    @Slot()
    def editOwner(self):
        dlg = OwnerDialog()
        dlg.exec()
        self.owner_combobox.clear()
        self.populateOwnerCombobox()

    def populateOwnerCombobox(self):
        self._owners: list = get_settings().get_owners()

        if self._owners is not None:
            for owner in self._owners:
                self.owner_combobox.addItem(owner)

    def setRefkey(self, last_refKey):
        new_refKey = increment_refKey(last_refKey)
        self.signage_refkey_lineedit.setText(new_refKey)

    def updateRefkeyField(self):
        signage_type = self.signage_type_combobox.currentText()
        prefix = self.signage_prefix_lineedit.text()
        if prefix == "":
            p = r"^\d+"
        else:
            p = f"^{prefix}"
        refkey = AppDatabase.fetchSignageLastRefkey(
            signage_type=signage_type, pattern=p
        )
        if refkey == "":
            refkey = f"{prefix}{0:03d}"
        self.setRefkey(refkey)

    def signage(self) -> Signage:
        """Return the new signage from the dialog"""
        new_signage = Signage(
            refkey=self.signage_refkey_lineedit.text(),
            title=self.signage_title_lineedit.toPlainText(),
            owner=self.owner_combobox.currentText(),
            type=self.signage_type_combobox.currentIndex(),
            due_date=self.due_date_edit.date()
        )
        return new_signage

    def accept(self):
        super().accept()


class OwnerDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Add/Remove Owner")

        self.list_widget = QtWidgets.QListWidget()
        self._owners: list = get_settings().get_owners()

        if self._owners is not None:
            for owner in self._owners:
                list_item = QtWidgets.QListWidgetItem()
                list_item.setText(owner)
                self.list_widget.addItem(list_item)

        self.owner_name = QtWidgets.QLineEdit()

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
        vbox.addWidget(self.owner_name)
        vbox.addLayout(hbox)

    def addListItem(self):
        """Add a single item to the list widget."""
        name = self.owner_name.text().strip()
        if name != "":
            list_item = QtWidgets.QListWidgetItem()
            list_item.setText(name)
            self.list_widget.addItem(list_item)
            self._owners.append(name)
            get_settings().set_owners(self._owners)
            self.owner_name.clear()

    def removeOneItem(self):
        """Remove a single item from the list widget."""
        row = self.list_widget.currentRow()
        item = self.list_widget.takeItem(row)
        self._owners.pop(row)
        get_settings().set_owners(self._owners)
        del item

    def showEvent(self, a0):
        self.adjustSize()
        return super().showEvent(a0)


class ExportDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

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
        self.destination_lineedit.setText(AppDatabase.activeWorkspace().rootpath)
        self.destination_lineedit.setReadOnly(True)

        # Signage type
        self.type_combobox = MultiCheckableComboBox()
        signage_type: SignageType
        for signage_type in AppDatabase.cache_signage_type.values():
            self.type_combobox.addItem(signage_type.name, signage_type)

        self.type_combobox.sigSelectionChanged.connect(self.updateButtonState)

        # Signage statuses
        self.status_combobox = MultiCheckableComboBox()
        signage_status: SignageStatus
        for signage_status in AppDatabase.cache_signage_status.values():
            self.status_combobox.addItem(signage_status.name, signage_status)

        # Public note
        self.public_note_checkbox = QtWidgets.QCheckBox("Export Public Note", self)

        # Options
        self.due_date_checkbox = QtWidgets.QCheckBox("Include Due date", self)
        self.due_date_checkbox.setChecked(False)

        # Standard buttons
        buttons = (
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # Forms
        form.addRow("Type", self.type_combobox)
        form.addRow("Status", self.status_combobox)
        form.addRow("Filename", filename_widget)
        form.addRow(self.destination_button, self.destination_lineedit)
        form.addRow("", self.public_note_checkbox)
        form.addRow("", self.due_date_checkbox)
        form.addWidget(self.buttonBox)

        self.updateButtonState()

    def updateButtonState(self):
        if (
            self.filename.text() != ""
            and self.destination_lineedit != ""
            and len(self.type_combobox.currentData()) > 0
        ):
            self.buttonBox.button(
                QtWidgets.QDialogButtonBox.StandardButton.Ok
            ).setEnabled(True)
        else:
            self.buttonBox.button(
                QtWidgets.QDialogButtonBox.StandardButton.Ok
            ).setEnabled(False)

    @Slot()
    def selectFolder(self):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(
            caption="",
            directory=AppDatabase.activeWorkspace().rootpath,
            options=QtWidgets.QFileDialog.Option.ShowDirsOnly,
        )
        if folder_path != "":
            self.destination_lineedit.setText(folder_path)
            self.updateButtonState()

    def accept(self):
        self.export_params = SignageExportParam(
            [value.name for value in self.type_combobox.currentData()],
            [value.name for value in self.status_combobox.currentData()],
            f"{self.destination_lineedit.text()}/{self.filename.text()}.xlsx",
            self.public_note_checkbox.isChecked(),
            self.due_date_checkbox.isChecked(),
        )
        super().accept()


class ImportDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._files = []

        form = QtWidgets.QFormLayout(self)
        self.setLayout(form)

        select_file_button = QtWidgets.QPushButton("Select Files")
        self.selected_file = QtWidgets.QLabel("0 files")
        select_file_button.clicked.connect(self.selectFiles)

        self.update_checkbox = QtWidgets.QCheckBox()
        self.update_checkbox.setCheckState(QtCore.Qt.CheckState.Unchecked)

        buttons = (
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        form.addRow(select_file_button, self.selected_file)
        form.addRow("Update Title", self.update_checkbox)
        form.addWidget(self.buttonBox)

        self.updateButtonState()

    @Slot()
    def selectFiles(self):
        files = QtWidgets.QFileDialog.getOpenFileNames(
            caption="Select files",
            directory=AppDatabase.activeWorkspace().rootpath,
            filter="*.xls*",
        )
        self._files = files[0]
        self.selected_file.setText(f"{len(self._files)} files")
        self.updateButtonState()

    def updateButtonState(self):
        if len(self._files) > 0:
            self.buttonBox.button(
                QtWidgets.QDialogButtonBox.StandardButton.Ok
            ).setEnabled(True)
        else:
            self.buttonBox.button(
                QtWidgets.QDialogButtonBox.StandardButton.Ok
            ).setEnabled(False)

    def selectedFiles(self):
        return self._files

    def accept(self):
        self.update_title = self.update_checkbox.isChecked()
        super().accept()
