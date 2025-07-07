from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


def is_dark_mode(app: QApplication):
    style_hints = app.styleHints()
    scheme = style_hints.colorScheme()
    return scheme == Qt.ColorScheme.Dark


app = QApplication([])


print(f'is dark mode = {is_dark_mode(app)}')