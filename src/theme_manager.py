import sys
from enum import Enum
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication, QPushButton
from PyQt6.QtGui import QPixmap, QPainter, QColor, QIcon
from PyQt6.QtCore import Qt, QSize


class Theme(Enum):
    LIGHT = "light"
    DARK = "dark"


def get_theme_color(theme: Theme) -> QColor:
    if theme == Theme.DARK:
        return QColor("#f0f0f0")  # light tint for dark background
    else:
        return QColor("#202020")  # dark tint for light background

def make_theme_icon(svg_path: str, theme: Theme, size: QSize = QSize(24, 24)) -> QIcon:
    color = get_theme_color(theme)

    try:
        renderer = QSvgRenderer(svg_path)
    except:
        print(f"❌ Cannot load resource: {svg_path}")
        return QIcon()
    
    if not renderer.isValid():
        print(f"❌ Cannot load resource: {svg_path}")
        return QIcon()

    svg_pixmap = QPixmap(size)
    svg_pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(svg_pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()

    color_pixmap = QPixmap(size)
    color_pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(color_pixmap)
    painter.fillRect(color_pixmap.rect(), color)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
    painter.drawPixmap(0, 0, svg_pixmap)
    painter.end()

    return QIcon(color_pixmap)


class ThemeIconManager:
    def __init__(self, theme: Theme = Theme.LIGHT):
        self.theme = theme
        self.icon_cache = {}  # (path, size) -> QIcon

    def get_icon(self, svg_path: str, size: QSize = QSize(24, 24)) -> QIcon:
        key = (svg_path, size, self.theme)
        if key not in self.icon_cache:
            self.icon_cache[key] = make_theme_icon(svg_path, self.theme, size)
        return self.icon_cache[key]

    def set_theme(self, theme: Theme):
        if self.theme != theme:
            self.theme = theme
            self.icon_cache.clear()  # refresh icons

    def get_theme(self) -> Theme:
        return self.theme
    
    def get_theme_color(self) -> QColor:
        return get_theme_color(self.theme)


theme_icon_manager = ThemeIconManager()


if __name__ == "__main__":
    from resources import qrc_resources
    theme_icon_manager = ThemeIconManager(Theme.DARK)
    print(f"color={theme_icon_manager.get_theme().value}")
    app = QApplication(sys.argv)
    view = QPushButton()
    ico = theme_icon_manager.get_icon(':file_add')
    view.setIcon(ico)

    view.show()
    sys.exit(app.exec())