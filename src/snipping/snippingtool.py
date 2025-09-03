from qtpy import (QtWidgets, Qt, QtGui, QtCore)
from utilities import config as mconf

class Capture(QtWidgets.QWidget):
    def __init__(self, source: str = None, parent=None):
        super(Capture, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

        self.global_final_origin = None
        self._cache_key = None
        self._source = source
        
        screen = self.screen()
        primary_screen = QtGui.QGuiApplication.primaryScreen()
        

        # Extend the widget area in multi monitors setup
        self.setGeometry(primary_screen.geometry().x(),
                         primary_screen.geometry().y(),
                         screen.geometry().width() + primary_screen.geometry().width(),
                         screen.geometry().height() + primary_screen.geometry().height())
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowOpacity(0.15)
        
        self.rubber_band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Shape.Rectangle, self)
        self.origin = QtCore.QPoint()

        # Delay the capture to ensure init
        QtCore.QTimer.singleShot(500, self.grabwindow)
    
    def showEvent(self, event):
        self.setCursor(Qt.CursorShape.CrossCursor)
        super().showEvent(event)
    
    def grabwindow(self):
        screen = self.screen()
        self.dpr = screen.devicePixelRatio()
        self.pixmap = screen.grabWindow(0)

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

    def cropArea(self, rect: QtCore.QRect) -> QtCore.QRect:
        """Calculate the x,y of the crop area relative to the screen coordinate"""
        x = rect.x()
        y = rect.y()
        
        if self.screen().geometry().x() != 0:
            x = abs(self.screen().geometry().x()) - abs(x)
            x = abs(x)
        
        if self.screen().geometry().y() != 0:
            y = abs(self.screen().geometry().y()) - abs(y)
            y = abs(y)
        
        crop_area = QtCore.QRect(int(x * self.dpr), 
                                 int(y * self.dpr), 
                                 int(rect.width() * self.dpr),
                                 int(rect.height() * self.dpr))

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

            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.close()
        super().mouseReleaseEvent(event)

    def capturekey(self) -> int:
        return self._cache_key