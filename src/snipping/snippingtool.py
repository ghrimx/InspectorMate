import time

from qtpy import (QtWidgets, Qt, QtGui, QtCore)
from utilities import config as mconf

class Capture(QtWidgets.QWidget):

    def __init__(self, source: str = None, parent = None):
        super().__init__(parent = parent)

        self._cache_key = None
        self._source = source

        self.global_final_origin = None
        
        self.setMouseTracking(True)
        desk_size = QtWidgets.QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(0, 0, desk_size.width(), desk_size.height())
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowOpacity(0.15)

        self.rubber_band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Shape.Rectangle, self)
        self.origin = QtCore.QPoint()

        QtWidgets.QApplication.setOverrideCursor(Qt.CursorShape.CrossCursor)
        screen = QtWidgets.QApplication.primaryScreen()
        rect = screen.virtualGeometry()

        time.sleep(0.31)
        self.pixmap = screen.grabWindow(0,
                                        rect.x(),
                                        rect.y(),
                                        rect.width(),
                                        rect.height())

    def mousePressEvent(self, event: QtGui.QMouseEvent | None) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.pos()
            self.global_initial_origin = event.globalPosition().toPoint()
        
            self.rubber_band.setGeometry(QtCore.QRect(self.origin, event.pos()).normalized())
            self.rubber_band.show() 

    def mouseMoveEvent(self, event: QtGui.QMouseEvent | None) -> None:
        if not self.origin.isNull():
            self.rubber_band.setGeometry(QtCore.QRect(self.origin, event.pos()).normalized())
            self.global_final_origin = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent | None) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.rubber_band.hide()

            if self.global_final_origin is not None:
                rect = QtCore.QRect(self.global_initial_origin, self.global_final_origin).normalized()

                self.pixmap = self.pixmap.copy(rect)

                # set clipboard
                clipboard = QtWidgets.QApplication.clipboard()
                clipboard.setPixmap(self.pixmap)

                self._cache_key = clipboard.pixmap().cacheKey()

                mconf.settings.setValue("capture", [self._cache_key, self._source])

            QtWidgets.QApplication.restoreOverrideCursor()
            self.close()

    def capturekey(self) -> int:
        return self._cache_key