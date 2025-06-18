import sys
import re
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QListWidget,
    QFileDialog, QMessageBox, QCheckBox, QComboBox, QListWidgetItem
)
from PyQt6.QtCore import Qt


class BatchRenameWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Batch File Renamer")
        self.resize(750, 520)

        self.files = []

        layout = QVBoxLayout(self)

        # File selection
        self.select_btn = QPushButton("📁 Select Files or Folder")
        self.select_btn.clicked.connect(self.select_files)
        layout.addWidget(self.select_btn)

        # Options layout
        options_layout = QHBoxLayout()

        self.num_chars_input = QLineEdit()
        self.num_chars_input.setPlaceholderText("# of chars")
        self.num_chars_input.setFixedWidth(80)

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
        options_layout.addWidget(QLabel("Prefix:"))
        options_layout.addWidget(self.prefix_input)
        options_layout.addWidget(QLabel("Suffix:"))
        options_layout.addWidget(self.suffix_input)
        layout.addLayout(options_layout)

        # Regex layout
        regex_layout = QHBoxLayout()
        self.regex_checkbox = QCheckBox("Use Regex")
        self.regex_pattern_input = QLineEdit()
        self.regex_pattern_input.setPlaceholderText("Regex Pattern")
        self.regex_repl_input = QLineEdit()
        self.regex_repl_input.setPlaceholderText("Replacement")

        regex_layout.addWidget(self.regex_checkbox)
        regex_layout.addWidget(self.regex_pattern_input)
        regex_layout.addWidget(self.regex_repl_input)
        layout.addLayout(regex_layout)

        # Checkboxes layout
        checkbox_layout = QHBoxLayout()
        self.include_dirs_checkbox = QCheckBox("Include Directory")
        self.recursive_checkbox = QCheckBox("Include Subfolders")
        self.dry_run_checkbox = QCheckBox("Dry Run (preview only)")

        checkbox_layout.addWidget(self.include_dirs_checkbox)
        checkbox_layout.addWidget(self.recursive_checkbox)
        checkbox_layout.addWidget(self.dry_run_checkbox)
        layout.addLayout(checkbox_layout)

        # Action buttons
        action_layout = QHBoxLayout()
        self.preview_btn = QPushButton("🔍 Preview")
        self.preview_btn.clicked.connect(self.preview_renames)

        self.rename_btn = QPushButton("✅ Rename")
        self.rename_btn.clicked.connect(self.rename_files)

        self.remove_btn = QPushButton("🗑 Remove Selected")
        self.remove_btn.clicked.connect(self.remove_selected_files)

        action_layout.addWidget(self.preview_btn)
        action_layout.addWidget(self.rename_btn)
        action_layout.addWidget(self.remove_btn)
        layout.addLayout(action_layout)

        # Preview list
        self.preview_list = QListWidget()
        self.preview_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.preview_list)

    def select_files(self):
        self.preview_list.clear()
        self.files = []

        if self.include_dirs_checkbox.isChecked():
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

        self.preview_list.addItems([
            f"📄 {f.name}" for f in self.files
        ])

    def preview_renames(self):
        try:
            count = int(self.num_chars_input.text()) if self.num_chars_input.text() else 0
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number for characters to replace.")
            return

        replacement = self.replace_input.text()
        prefix = self.prefix_input.text()
        suffix = self.suffix_input.text()
        position = self.position_box.currentText()

        use_regex = self.regex_checkbox.isChecked()
        regex_pattern = self.regex_pattern_input.text()
        regex_replacement = self.regex_repl_input.text()

        self.preview_list.clear()
        self.rename_pairs = []

        for path in self.files:
            name = path.stem
            ext = path.suffix

            try:
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
                    self.preview_list.addItem(f"📄 {path.name} → {new_path.name}")
            except re.error as e:
                QMessageBox.critical(self, "Regex Error", f"Invalid regex:\n{e}")
                return

    def rename_files(self):
        if not hasattr(self, 'rename_pairs'):
            QMessageBox.information(self, "No Preview", "Please run a preview before renaming.")
            return

        renamed_count = 0

        for src, dst in self.rename_pairs:
            if self.dry_run_checkbox.isChecked():
                continue
            try:
                if src != dst and not dst.exists():
                    src.rename(dst)
                    renamed_count += 1
            except Exception as e:
                QMessageBox.critical(self, "Rename Error", f"Failed to rename {src.name}:\n{e}")

        QMessageBox.information(self, "Done", f"{'Simulated' if self.dry_run_checkbox.isChecked() else 'Renamed'} {renamed_count} files.")
        self.preview_list.clear()

    def remove_selected_files(self):
        selected_items = self.preview_list.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            text = item.text()
            old_name = text.split(" → ")[0].strip("📄 ").strip()
            self.files = [f for f in self.files if f.name != old_name]
            self.preview_list.takeItem(self.preview_list.row(item))

        if hasattr(self, 'rename_pairs'):
            del self.rename_pairs


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = BatchRenameWidget()
    widget.show()
    sys.exit(app.exec())
