import sys
import re
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QListWidget,
    QFileDialog, QMessageBox, QCheckBox, QComboBox, QListWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt


class BatchRenameWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Batch File Renamer")
        self.resize(750, 520)

        layout = QVBoxLayout(self)

        # File selection
        self.select_btn = QPushButton("📁 Select Files or Folder")
        # self.include_dirs_checkbox = QCheckBox("Include Directory")
        self.recursive_checkbox = QCheckBox("Include Subfolders")
        # self.select_btn.clicked.connect(self.select_files)
        layout.addWidget(self.select_btn)
        # layout.addWidget(self.include_dirs_checkbox)
        layout.addWidget(self.recursive_checkbox)

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
        self.regex_repl_input = QLineEdit()
        self.regex_repl_input.setPlaceholderText("Replacement")

        regex_layout.addWidget(self.regex_checkbox)
        regex_layout.addWidget(self.regex_pattern_input)
        regex_layout.addWidget(self.regex_repl_input)
        layout.addLayout(regex_layout)

        # Checkboxes layout
        checkbox_layout = QHBoxLayout()
        self.dry_run_checkbox = QCheckBox("Dry Run (preview only)")
        checkbox_layout.addWidget(self.dry_run_checkbox)
        layout.addLayout(checkbox_layout)

        splitter = QSplitter()

        # Source list
        src_widget = QWidget()
        src_layout = QVBoxLayout()
        src_widget.setLayout(src_layout)
        src_layout.addWidget(QLabel("Source:"))
        self.src_list = QListWidget()
        self.src_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        src_layout.addWidget(self.src_list)

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
        # self.rename_btn.clicked.connect(self.rename_files)

        self.remove_btn = QPushButton("🗑 Remove Selected")
        # self.remove_btn.clicked.connect(self.remove_selected_files)

        action_layout.addWidget(self.rename_btn)
        action_layout.addWidget(self.remove_btn)
        layout.addLayout(action_layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = BatchRenameWidget()
    widget.show()
    sys.exit(app.exec())