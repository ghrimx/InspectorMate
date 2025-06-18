import sys
import re
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QListWidget,
    QFileDialog, QMessageBox, QCheckBox, QComboBox, QSplitter
)
from PyQt6.QtCore import Qt, QItemSelectionModel, pyqtSlot as Slot
from PyQt6.QtGui import QIntValidator

class BatchRenameWidget(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Batch File Renamer")
        self.resize(750, 520)

        self.files = []

        layout = QVBoxLayout(self)

        # File selection
        self.select_btn = QPushButton("📁 Select Files or Folder")
        self.folder_only_checkbox = QCheckBox("Show Folder only")
        self.recursive_checkbox = QCheckBox("Include Subfolders")
        self.recursive_checkbox.setEnabled(False)
        self.select_btn.clicked.connect(self.select_files)
        layout.addWidget(self.select_btn)
        layout.addWidget(self.folder_only_checkbox)
        layout.addWidget(self.recursive_checkbox)

        self.folder_only_checkbox.checkStateChanged.connect(self.update_checkbox)

        # Options layout
        options_layout = QHBoxLayout()

        self.num_chars_input = QLineEdit()
        self.num_chars_input.setPlaceholderText("# of chars")
        self.num_chars_input.setFixedWidth(80)

        validator = QIntValidator(0, 999)
        self.num_chars_input.setValidator(validator)

        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replacement")

        self.position_box = QComboBox()
        self.position_box.addItems(["Replace Leading", "Replace Trailing"])
        self.position_box.setFixedWidth(130)

        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("Prefix")

        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("Suffix")

        options_layout.addWidget(QLabel("Replace:"))
        options_layout.addWidget(self.num_chars_input)
        options_layout.addWidget(self.replace_input)
        options_layout.addWidget(self.position_box)
        layout.addLayout(options_layout)

        # Add string
        add_str_layout = QHBoxLayout()
        add_str_layout.addWidget(QLabel("Prefix:"))
        add_str_layout.addWidget(self.prefix_input)
        add_str_layout.addWidget(QLabel("Suffix:"))
        add_str_layout.addWidget(self.suffix_input)
        layout.addLayout(add_str_layout)

        # Regex layout
        regex_layout = QHBoxLayout()
        self.regex_checkbox = QCheckBox("Use Regex")
        self.regex_pattern_input = QLineEdit()
        self.regex_pattern_input.setPlaceholderText("Regex Pattern")
        spacer = QLabel('>>>')
        self.regex_repl_input = QLineEdit()
        self.regex_repl_input.setPlaceholderText("Replacement")
        self.error_regex = QLabel()
        self.error_regex.setFixedHeight(15)
        self.error_regex.setMargin(0)
        self.error_regex.setStyleSheet("QLabel { color : red; }")

        regex_layout.addWidget(self.regex_checkbox)
        regex_layout.addWidget(self.regex_pattern_input)
        regex_layout.addWidget(spacer)
        regex_layout.addWidget(self.regex_repl_input)
        layout.addLayout(regex_layout)
        layout.addWidget(self.error_regex)

        splitter = QSplitter()

        # Source list
        src_widget = QWidget()
        src_layout = QVBoxLayout()
        src_widget.setLayout(src_layout)
        src_layout.addWidget(QLabel("Source:"))
        self.src_list = QListWidget()
        self.src_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        src_layout.addWidget(self.src_list)

        self.src_list.itemSelectionChanged.connect(self.sync_selection_to_renamed)

        # Dest list
        dst_widget = QWidget()
        dst_layout = QVBoxLayout()
        dst_widget.setLayout(dst_layout)
        dst_layout.addWidget(QLabel("Destination:"))
        self.dst_list = QListWidget()
        dst_layout.addWidget(self.dst_list)

        splitter.addWidget(src_widget)
        splitter.addWidget(dst_widget)

        layout.addWidget(splitter)

        # Action buttons
        action_layout = QHBoxLayout()

        self.rename_btn = QPushButton("✅ Rename")
        self.rename_btn.clicked.connect(self.rename_files)

        self.remove_btn = QPushButton("🗑 Remove Selected")
        # self.remove_btn.clicked.connect(self.remove_selected_files)

        action_layout.addWidget(self.rename_btn)
        action_layout.addWidget(self.remove_btn)
        layout.addLayout(action_layout)

        self.num_chars_input.textChanged.connect(self.preview_renames)
        self.replace_input.textChanged.connect(self.preview_renames)
        self.prefix_input.textChanged.connect(self.preview_renames)
        self.suffix_input.textChanged.connect(self.preview_renames)
        self.regex_pattern_input.textChanged.connect(self.preview_renames)
        self.regex_repl_input.textChanged.connect(self.preview_renames)
        self.position_box.currentIndexChanged.connect(self.preview_renames)
        self.regex_checkbox.stateChanged.connect(self.preview_renames)

    @Slot(Qt.CheckState)
    def update_checkbox(self, state: Qt.CheckState):
        self.recursive_checkbox.setEnabled(state.value)

    def select_files(self):
        self.src_list.clear()
        self.dst_list.clear()
        
        if self.folder_only_checkbox.isChecked():
            dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
            if dir_path:
                base = Path(dir_path)
                if self.recursive_checkbox.isChecked():
                    self.files = [p for p in base.rglob('*') if p.is_file()]
                else:
                    self.files = [p for p in base.iterdir() if p.is_file()]
        else:
            file_paths, _ = QFileDialog.getOpenFileNames(self, "Select Files")
            if file_paths:
                self.files = [Path(p) for p in file_paths]

        self.src_list.addItems([f.name for f in self.files])
        self.dst_list.addItems([f.name for f in self.files])

    def sync_selection_to_renamed(self):
        self.dst_list.clearSelection()
        for index in self.src_list.selectedIndexes():
            self.dst_list.setCurrentRow(index.row(), QItemSelectionModel.SelectionFlag.Select)
           
    def preview_renames(self):
        if not self.files:
            return
        
        count = int(self.num_chars_input.text()) if self.num_chars_input.text() else 0

        replacement = self.replace_input.text()
        prefix = self.prefix_input.text()
        suffix = self.suffix_input.text()
        position = self.position_box.currentText()

        use_regex = self.regex_checkbox.isChecked()
        regex_pattern = self.regex_pattern_input.text()
        regex_replacement = self.regex_repl_input.text()

        self.rename_pairs = []
        self.dst_list.clear()
        self.dst_list.addItems([f.name for f in self.files])

        for i in range(self.dst_list.count()):
            item = self.dst_list.item(i)
            path = self.files[i]
            name = path.stem
            ext = path.suffix

            try:
                self.error_regex.setText('')
                if use_regex:
                    name = re.sub(regex_pattern, regex_replacement, name)
                elif count > 0:
                    if position == "Replace Leading":
                        name = replacement + name[count:]
                    else:
                        name = name[:-count] + replacement if count <= len(name) else replacement

                name = prefix + name + suffix
                new_path = path.with_name(name + ext)

                if path != new_path:
                    self.rename_pairs.append((path, new_path))
                    item.setText(new_path.name)
            except re.error as e:
                self.error_regex.setText(f"Invalid regex: {e}")
                return

    def rename_files(self):
        renamed_count = 0

        for src, dst in self.rename_pairs:
            try:
                if src != dst and not dst.exists():
                    src.rename(dst)
                    renamed_count += 1
            except Exception as e:
                QMessageBox.critical(self, "Rename Error", f"Failed to rename {src.name}:\n{e}")

        QMessageBox.information(self, "Done", f"Renamed {renamed_count} files.")

        self.rename_pairs.clear()
        self.files.clear()
        self.src_list.clear()
        self.dst_list.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = BatchRenameWidget()
    widget.show()
    sys.exit(app.exec())