from pathlib import Path
from PyQt6.QtWidgets import (QDialog,
                             QVBoxLayout,
                             QPushButton,
                             QHBoxLayout,
                             QComboBox,
                             QCheckBox,
                             QLineEdit,
                             QLabel,
                             QListWidget,
                             QFileDialog,
                             QMessageBox)


class BatchRenameWidget(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Batch File Renamer")
        self.resize(700, 500)

        self.files = []

        layout = QVBoxLayout(self)

        # File selection
        self.select_btn = QPushButton("📁 Select Files")
        self.select_btn.clicked.connect(self.select_files)
        layout.addWidget(self.select_btn)

        # Input options
        options_layout = QHBoxLayout()

        self.num_chars_input = QLineEdit()
        self.num_chars_input.setPlaceholderText("# of chars")
        self.num_chars_input.setFixedWidth(80)

        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replacement")

        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("Prefix")

        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("Suffix")

        self.position_box = QComboBox()
        self.position_box.addItems(["Replace Leading", "Replace Trailing"])
        self.position_box.setFixedWidth(130)

        options_layout.addWidget(QLabel("Replace:"))
        options_layout.addWidget(self.num_chars_input)
        options_layout.addWidget(self.replace_input)
        options_layout.addWidget(self.position_box)
        options_layout.addWidget(QLabel("Prefix:"))
        options_layout.addWidget(self.prefix_input)
        options_layout.addWidget(QLabel("Suffix:"))
        options_layout.addWidget(self.suffix_input)
        layout.addLayout(options_layout)

        # Checkboxes
        checkbox_layout = QHBoxLayout()
        self.dry_run_checkbox = QCheckBox("Dry Run (preview only)")
        checkbox_layout.addWidget(self.dry_run_checkbox)
        layout.addLayout(checkbox_layout)

        # Buttons
        action_layout = QHBoxLayout()
        self.preview_btn = QPushButton("🔍 Preview")
        self.preview_btn.clicked.connect(self.preview_renames)

        self.rename_btn = QPushButton("✅ Rename")
        self.rename_btn.clicked.connect(self.rename_files)

        action_layout.addWidget(self.preview_btn)
        action_layout.addWidget(self.rename_btn)
        layout.addLayout(action_layout)

        # Preview list
        self.preview_list = QListWidget()
        layout.addWidget(self.preview_list)

    def select_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        if file_paths:
            self.files = [Path(p) for p in file_paths]
            self.preview_list.clear()
            self.preview_list.addItems([f.name for f in self.files])

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

        self.preview_list.clear()
        self.rename_pairs = []

        for path in self.files:
            name = path.stem
            ext = path.suffix

            # Replace leading/trailing
            if count > 0:
                if position == "Replace Leading":
                    name = replacement + name[count:]
                else:  # trailing
                    name = name[:-count] + replacement if count <= len(name) else replacement
            # Add prefix/suffix
            name = prefix + name + suffix

            new_path = path.with_name(name + ext)
            self.rename_pairs.append((path, new_path))
            self.preview_list.addItem(f"{path.name} → {new_path.name}")

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



