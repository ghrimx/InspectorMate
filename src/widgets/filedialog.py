import logging

from qtpy import (QtWidgets, Slot, Signal, QtCore)
from database.database import AppDatabase
from utilities.utils import (mergeExcelFiles, unpackZip)
from utilities.decorators import status_signal

from widgets.fileselectiondialog import selectFilesDialog

logger = logging.getLogger(__name__)

class WorkerSignals(QtCore.QObject):
    result = Signal(object)
    error = Signal(Exception)
    finished = Signal(str)
    status = Signal(str)


class Runnable(QtCore.QRunnable):
    def __init__(self, func):
        super().__init__()
        self.func = func
        self.signals = WorkerSignals()

    def run(self):
        try:
            self.func()
        except Exception as e:
            msg = "❌ An error occured!"
            self.signals.error.emit(e)
        else:
            msg = "✔️ Done!"
        finally:
            self.signals.finished.emit(msg)


class ConcatExcelDialog(QtWidgets.QDialog):
    def __init__(self, start_process: callable=None, process_ended: callable=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Concatenate Excel files")
        self.start_process = start_process
        self.process_ended = process_ended

        self._files = []
        self._duplicate_option: str | bool = "first"

        form = QtWidgets.QFormLayout(self)
        self.setLayout(form)

        select_file_button = QtWidgets.QPushButton("Select Files")
        self.selected_file = QtWidgets.QLabel("0 files")
        select_file_button.clicked.connect(self.selectFiles)

        duplicate_widget = QtWidgets.QWidget()
        duplicate_widget_layout = QtWidgets.QHBoxLayout()
        duplicate_widget.setLayout(duplicate_widget_layout)

        drop_first_duplicate = QtWidgets.QRadioButton("first")
        drop_first_duplicate.setChecked(True)
        drop_first_duplicate.toggled.connect(lambda: self.radioStateChanged("first"))
        drop_first_duplicate.setToolTip("Drop duplicates except for the first occurrence")
        drop_last_duplicate = QtWidgets.QRadioButton("last")
        drop_last_duplicate.setChecked(False)
        drop_last_duplicate.setToolTip("Drop duplicates except for the last occurrence")
        drop_last_duplicate.toggled.connect(lambda: self.radioStateChanged("last"))
        keep_duplicate = QtWidgets.QRadioButton("drop all")
        keep_duplicate.setChecked(False)
        keep_duplicate.toggled.connect(lambda: self.radioStateChanged(False))
        keep_duplicate.setToolTip("Drop all duplicates")

        duplicate_widget_layout.addWidget(drop_first_duplicate)
        duplicate_widget_layout.addWidget(drop_last_duplicate)
        duplicate_widget_layout.addWidget(keep_duplicate)
        duplicate_widget_layout.addStretch()
        duplicate_widget_layout.setContentsMargins(0,0,0,0)

        filename_widget = QtWidgets.QWidget()
        filename_layout = QtWidgets.QHBoxLayout()
        filename_widget.setLayout(filename_layout)
        
        self.filename = QtWidgets.QLineEdit(self)
        self.filename.setText("output")
        self.filename.setMinimumWidth(300)
        self.filename.textChanged.connect(self.updateButtonState)

        filename_layout.addWidget(self.filename)
        filename_layout.addWidget(QtWidgets.QLabel(".xlsx"))
        filename_layout.setContentsMargins(0,0,0,0)

        self.destination_button = QtWidgets.QPushButton("Destination")
        self.destination_button.clicked.connect(self.selectFolder)
        self.destination = QtWidgets.QLineEdit(self)
        self.destination.setText(AppDatabase.activeWorkspace().rootpath)
        self.destination.setReadOnly(True)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        form.addRow(select_file_button, self.selected_file)
        form.addRow("Duplicate", duplicate_widget)
        form.addRow("Outfile", filename_widget)
        form.addRow(self.destination_button, self.destination)
        form.addWidget(self.buttonBox)

        self.updateButtonState()

    def updateButtonState(self):
        if self.filename.text() != "" and self.destination.text() != "" and len(self._files) > 0:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(False)
    
    @Slot()
    def selectFiles(self):
        self._files = selectFilesDialog("*.xls*", AppDatabase.activeWorkspace().rootpath)
        self.selected_file.setText(f"{len(self._files)} files")
        self.updateButtonState()

    @Slot()
    def selectFolder(self):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(caption='',
                                                                 directory=AppDatabase.activeWorkspace().rootpath,
                                                                 options=QtWidgets.QFileDialog.Option.ShowDirsOnly)
        if folder_path != "":
            self.destination.setText(folder_path)
            self.updateButtonState()

    @Slot()
    def radioStateChanged(self, option: str | bool):
        self._duplicate_option = option

    def accept(self):
        pool = QtCore.QThreadPool().globalInstance()

        outfile = f"{self.destination.text()}/{self.filename.text()}.xlsx"

        def merge():
            mergeExcelFiles(self._files,
                            self._duplicate_option,
                            outfile)
        
        self.start_process("Merging...")
        runnable = Runnable(merge)
        runnable.signals.error.connect(lambda e: logger.error(e))
        runnable.signals.finished.connect(lambda msg: self.process_ended(msg))
        pool.start(runnable)

        super().accept()


class UnzipDialog(QtWidgets.QDialog):
    def __init__(self, source: str = None, dest: str = None, start_process: callable=None, process_ended: callable=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Unzip archive")
        self.start_process = start_process
        self.process_ended = process_ended

        self._files = []

        self._source_dir = source
        self._dest = dest

        select_file_button = QtWidgets.QPushButton("Select Files")
        self.selected_file = QtWidgets.QLabel("0 files")
        select_file_button.clicked.connect(self.selectFiles)

        form = QtWidgets.QFormLayout(self)
        self.setLayout(form)

        self.destination_button = QtWidgets.QPushButton("Destination")
        self.destination_button.clicked.connect(self.selectFolder)
        self.destination = QtWidgets.QLineEdit(self)
        self.destination.setText(self._dest)
        self.destination.setMinimumWidth(300)
        self.destination.setReadOnly(True)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        form.addRow(select_file_button, self.selected_file)
        form.addRow(self.destination_button, self.destination)
        form.addWidget(self.buttonBox)

        self.selectFiles()

    def updateButtonState(self):
        if self.destination.text() != "" and len(self._files) > 0:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(False)
    
    @Slot()
    def selectFiles(self):
        self._files = selectFilesDialog("*.zip", self._source_dir)
        self.selected_file.setText(f"{len(self._files)} files")
        self.updateButtonState()

    @Slot()
    def selectFolder(self):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(caption='',
                                                                 directory=self._source_dir,
                                                                 options=QtWidgets.QFileDialog.Option.ShowDirsOnly)
        if folder_path != "":
            self.destination.setText(folder_path)
            self.updateButtonState()

    def accept(self):
        pool = QtCore.QThreadPool().globalInstance()
        destination = self.destination.text()

        def unzip():
            for files in self._files:
                unpackZip(files, destination)
        
        self.start_process("Unzipping...")
        runnable = Runnable(unzip)
        runnable.signals.error.connect(lambda e: logger.error(e))
        runnable.signals.finished.connect(lambda msg: self.process_ended(msg))

        pool.start(runnable)

        super().accept()