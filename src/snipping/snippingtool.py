from qtpy import (QtWidgets, Qt, QtGui, QtCore)
from utilities import config as mconf

class Capture(QtWidgets.QWidget):
    def __init__(self, source: str = None, parent=None):
        super(Capture, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.unsetCursor()

        self.global_final_origin = None
        self._cache_key = None
        self._source = source

        # Cover *all* monitors
        desktop_geometry = QtGui.QGuiApplication.primaryScreen().virtualGeometry()
        self.setGeometry(desktop_geometry)

        self.setWindowFlags(
            self.windowFlags() 
            | Qt.WindowType.FramelessWindowHint 
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowOpacity(0.15)

        self.rubber_band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Shape.Rectangle, self)
        self.origin = QtCore.QPoint()
    
    def showEvent(self, event):
        super().showEvent(event)
        QtWidgets.QApplication.setOverrideCursor(Qt.CursorShape.CrossCursor)

    def closeEvent(self, event):
        QtWidgets.QApplication.restoreOverrideCursor()
        super().closeEvent(event)
    
    def mousePressEvent(self, event: QtGui.QMouseEvent | None) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.pos()
            self.global_initial_origin = event.globalPosition().toPoint()

            screen = QtGui.QGuiApplication.screenAt(self.global_initial_origin)
            self.pixmap = screen.grabWindow(0)
            self.dpr = self.pixmap.devicePixelRatio()
            self.screen_geometry = screen.geometry()
            
            self.rubber_band.setGeometry(QtCore.QRect(self.origin, event.pos()).normalized())
            self.rubber_band.show() 

    def mouseMoveEvent(self, event: QtGui.QMouseEvent | None) -> None:
        if not self.origin.isNull():
            self.rubber_band.setGeometry(QtCore.QRect(self.origin, event.pos()).normalized())
            self.global_final_origin = event.globalPosition().toPoint()

    def cropArea(self, rect: QtCore.QRect) -> QtCore.QRect:
        """Convert global QRect to device-pixel coordinates for cropping"""

        # Translate global rect into local screen coords
        local_rect = rect.translated(-self.screen_geometry.topLeft())

        # Apply DPR scaling
        crop_area = QtCore.QRect(
            int(local_rect.x() * self.dpr),
            int(local_rect.y() * self.dpr),
            int(local_rect.width() * self.dpr),
            int(local_rect.height() * self.dpr),
        )
        return crop_area

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent | None) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.rubber_band.hide()

            if self.global_final_origin is not None:
                crop = QtCore.QRect(self.global_initial_origin, self.global_final_origin).normalized()

                corrected_crop = self.cropArea(crop)

                self.pixmap = self.pixmap.copy(corrected_crop)

                # set clipboard
                clipboard = QtWidgets.QApplication.clipboard()
                clipboard.setPixmap(self.pixmap)

                self._cache_key = clipboard.pixmap().cacheKey()

                mconf.settings.setValue("capture", [self._cache_key, self._source])

            self.close()
        super().mouseReleaseEvent(event)

    def capturekey(self) -> int:
        return self._cache_key