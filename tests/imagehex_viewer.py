import sys
import base64
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton
from PyQt6.QtGui import QPixmap, QIcon

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")

        widget = QWidget()
        self.setCentralWidget(widget)

        vbox = QVBoxLayout()
        widget.setLayout(vbox)

        self.path_linedit = QLineEdit()
        self.image_area = QLabel()
        self.hex_area = QTextEdit()
        self.load_button = QPushButton()
        self.load_button.setText("load hex")

        vbox.addWidget(self.path_linedit)
        vbox.addWidget(self.image_area)
        vbox.addWidget(self.hex_area)
        vbox.addWidget(self.load_button)

        self.path_linedit.textChanged.connect(self.loadImage)
        self.load_button.clicked.connect(self.loadHex)

    def loadImage(self):
        fpath = self.path_linedit.text()
        img_binary = self.path2bin(fpath)
        img_64str = self.bin2Img64Str(img_binary)
        icon: QIcon = self.hex2Icon(img_64str)

        self.image_area.setPixmap(icon.pixmap(32, 32))
        self.hex_area.setText(img_64str.strip())

    def path2bin(self, filename): 
        fpath = Path(filename)
        try:
            with open(fpath.as_posix(), 'rb') as file: 
                blobData = file.read() 
            return blobData 
        except:
            ...
    
    def bin2Img64Str(self, bin):
        return base64.b64encode(bin).decode('utf-8')
    
    def hex2Icon(self, imge64str: str):
        hex = base64.b64decode(imge64str)
        pixmap = QPixmap()
        pixmap.loadFromData(hex)
        icon = QIcon(pixmap)
        return icon
    
    def loadHex(self):
        img_hex = self.hex_area.toPlainText()
        icon = self.hex2Icon(img_hex)
        self.image_area.setPixmap(icon.pixmap(32, 32))

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()