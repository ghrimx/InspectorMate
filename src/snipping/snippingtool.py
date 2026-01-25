from qtpy import (QtWidgets, Qt, QtGui, QtCore)
from utilities import config as mconf
from urllib import parse
import base64

def make_cf_html(fragment: str) -> bytes:
    fragment = fragment.strip()

    html = (
        "<html><body>"
        "<!--StartFragment-->"
        f"{fragment}"
        "<!--EndFragment-->"
        "</body></html>"
    )

    html_bytes = html.encode("utf-8")

    header = (
        "Version:1.0\r\n"
        "StartHTML:{:08d}\r\n"
        "EndHTML:{:08d}\r\n"
        "StartFragment:{:08d}\r\n"
        "EndFragment:{:08d}\r\n"
    )

    # Temporary header to compute byte offsets
    header_bytes = header.format(0, 0, 0, 0).encode("ascii")

    start_html = len(header_bytes)
    start_fragment = html_bytes.index(b"<!--StartFragment-->") + len(b"<!--StartFragment-->") + start_html
    end_fragment = html_bytes.index(b"<!--EndFragment-->") + start_html
    end_html = start_html + len(html_bytes)

    final_header = header.format(
        start_html,
        end_html,
        start_fragment,
        end_fragment,
    ).encode("ascii")

    return final_header + html_bytes


import base64
from urllib import parse

from PyQt6 import QtCore, QtGui, QtWidgets


class ClipboardExporter:
    """
    Export image + caption (as file link) to the system clipboard.

    Optimized for:
    - PyQt6 QTextEdit
    - Word / LibreOffice
    - Outlook

    Graceful fallback:
    - text/plain
    - image/*
    - text/uri-list
    """

    _last_mime = None  # prevent GC on Windows

    @staticmethod
    def copy_capture(
        pixmap: QtGui.QPixmap,
        caption: str,
        source_file: str,
    ):
        clipboard = QtWidgets.QApplication.clipboard()

        def _do_copy():
            mime = QtCore.QMimeData()

            # ---------- Plain text fallback ----------
            if caption:
                mime.setText(caption)

            # ---------- Image ----------
            mime.setImageData(pixmap.toImage())

            # ---------- URI list (important for Windows apps) ----------
            if source_file:
                url = QtCore.QUrl.fromLocalFile(source_file)
                mime.setUrls([url])

            # ---------- Encode pixmap ----------
            ba = QtCore.QByteArray()
            buffer = QtCore.QBuffer(ba)
            buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
            pixmap.save(buffer, "PNG")

            img_base64 = base64.b64encode(ba.data()).decode("ascii")

            # ---------- Build HTML (Qt-friendly) ----------
            href = "file:///" + parse.quote(source_file.replace("\\", "/"))

            html = (
                "<html><body>"
                f"<img src='data:image/png;base64,{img_base64}'><br>"
                f"<a href='{href}'>{caption}</a>"
                "</body></html>"
            )

            mime.setHtml(html)

            mime.setText(f"<a href='{href}'>{caption}</a>")

            # ---------- Keep alive + set ----------
            ClipboardExporter._last_mime = mime
            clipboard.setMimeData(mime)

        # Delay to avoid OLE race conditions
        QtCore.QTimer.singleShot(0, _do_copy)



class Capture(QtWidgets.QWidget):
    def __init__(self, caption: str = None, uri: str = None, parent=None):
        super(Capture, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.unsetCursor()

        self.global_final_origin = None
        self._cache_key = None
        self.caption = caption
        self._uri = uri

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
                # clipboard = QtWidgets.QApplication.clipboard()
                # clipboard.setPixmap(self.pixmap)

                self.copy_pixmap_with_text(self.pixmap)

                # self._cache_key = clipboard.pixmap().cacheKey()

                mconf.settings.setValue("capture", [self._cache_key, self.caption])

            self.close()
        super().mouseReleaseEvent(event)

    def capturekey(self) -> int:
        return self._cache_key
    
    def copy_pixmap_with_text(self, pixmap: QtGui.QPixmap):
        ClipboardExporter.copy_capture(
            pixmap=pixmap,
            caption=self.caption,
            source_file=self._uri,
        )
