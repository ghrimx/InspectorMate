import json
import base64
from urllib import parse

from qtpy import (QtWidgets, QtGui, QtCore)


class ClipboardExporter:
    _last_mime = None  # prevent GC on Windows

    @staticmethod
    def toClipboard(src_file: str, caption = "", anchor: dict = None, pixmap: QtGui.QPixmap = None):
        clipboard = QtWidgets.QApplication.clipboard()

        def _do_copy():
            mime = QtCore.QMimeData()

            url = QtCore.QUrl.fromLocalFile(src_file)
            href = url.toString()

            if anchor:
                page = anchor.get("page", "?")
                hlink = f'<a href="{href}#page={page}">{caption}</a>'
            else:
                hlink = f'<a href="{href}">{caption}</a>'

            if pixmap:
                mime.setImageData(pixmap.toImage())

                # Encode pixmap
                ba = QtCore.QByteArray()
                buffer = QtCore.QBuffer(ba)
                buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
                pixmap.save(buffer, "PNG")

                img_base64 = base64.b64encode(ba.data()).decode("ascii")

                # Build HTML for other application than InspectorMate
                href = "file:///" + parse.quote(src_file.replace("\\", "/"))

                html = (
                    "<html><body>"
                    f"<img src='data:image/png;base64,{img_base64}'><br>"
                    f"{hlink}"
                    "</body></html>"
                )
            else:
                html = hlink

            mime.setText(caption) # Text to display
            mime.setUrls([url]) # link to source file
            mime.setHtml(html)

            if anchor:
                mime.setData("application/x-inspectormate-anchor",
                             QtCore.QByteArray(json.dumps(anchor).encode("utf-8")))

            ClipboardExporter._last_mime = mime
            clipboard.setMimeData(mime)

        # Delay to avoid OLE race conditions
        QtCore.QTimer.singleShot(0, _do_copy)

