import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QPushButton, QVBoxLayout, QWidget
from PyQt6.QAxContainer import QAxWidget


class OfficeViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ax = QAxWidget(self)
        self.ax.setControl("Shell.Explorer")  # Alternative: "Word.Application" or "PowerPoint.Application"
        self.ax.setObjectName("office_viewer")
        self.ax.setFixedSize(800, 600)

        layout = QVBoxLayout(self)
        layout.addWidget(self.ax)

    def load_office_file(self, filepath: str):
        self.ax.dynamicCall("Navigate(const QString&)", filepath)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Office Document Viewer")
        self.setFixedSize(850, 650)

        self.viewer = OfficeViewer(self)
        self.setCentralWidget(self.viewer)

        # Load document button
        load_btn = QPushButton("Open Word/PowerPoint File")
        load_btn.clicked.connect(self.open_file)
        self.viewer.layout().insertWidget(0, load_btn)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Office Document",
            "",
            "Office Files (*.docx *.pptx *.doc *.ppt);;All Files (*)"
        )

        if file_path:
            self.viewer.load_office_file(file_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
