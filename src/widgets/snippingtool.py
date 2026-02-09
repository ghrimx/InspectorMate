from qtpy import (QtWidgets, Qt, QtGui, QtCore)


class Screenshot(QtWidgets.QWidget):
    captured = QtCore.pyqtSignal(QtGui.QPixmap)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.origin = QtCore.QPoint()
        self.global_initial_origin = None
        self.global_final_origin = None

        self.pixmap = None
        self.dpr = 1.0
        self.screen_geometry = None

        # Cover all monitors
        geo = QtGui.QGuiApplication.primaryScreen().virtualGeometry()
        self.setGeometry(geo)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowOpacity(0.15)

        self.rubber_band = QtWidgets.QRubberBand(
            QtWidgets.QRubberBand.Shape.Rectangle, self
        )

    def showEvent(self, event):
        super().showEvent(event)
        QtWidgets.QApplication.setOverrideCursor(Qt.CursorShape.CrossCursor)

    def closeEvent(self, event):
        QtWidgets.QApplication.restoreOverrideCursor()
        super().closeEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        self.origin = event.pos()
        self.global_initial_origin = event.globalPosition().toPoint()

        screen = QtGui.QGuiApplication.screenAt(self.global_initial_origin)
        if not screen:
            return

        self.pixmap = screen.grabWindow(0)
        self.dpr = self.pixmap.devicePixelRatio()
        self.screen_geometry = screen.geometry()

        self.rubber_band.setGeometry(QtCore.QRect(self.origin, self.origin))
        self.rubber_band.show()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.origin.isNull():
            return

        self.global_final_origin = event.globalPosition().toPoint()
        rect = QtCore.QRect(self.origin, event.pos()).normalized()
        self.rubber_band.setGeometry(rect)

    def _crop_area(self, global_rect: QtCore.QRect) -> QtCore.QRect:
        """Convert global rect to device-pixel rect"""

        local = global_rect.translated(-self.screen_geometry.topLeft())

        return QtCore.QRect(
            int(local.x() * self.dpr),
            int(local.y() * self.dpr),
            int(local.width() * self.dpr),
            int(local.height() * self.dpr),
        )

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            
            self.rubber_band.hide()

            if self.pixmap and self.global_final_origin:
                rect = QtCore.QRect(
                    self.global_initial_origin,
                    self.global_final_origin,
                ).normalized()

                crop = self._crop_area(rect)
                result = self.pixmap.copy(crop)

                if not result.isNull():
                    self.captured.emit(result)

            self.close()

        super().mouseReleaseEvent(event)
