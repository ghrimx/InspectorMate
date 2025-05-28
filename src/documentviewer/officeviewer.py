import logging
from qtpy import (QtWidgets, Slot)

from PyMuPDF4QT.pymupdfviewer import PdfViewer
from evidence.evidencemodel import Document

from widgets.waitingspinner import WaitingSpinner


logger = logging.getLogger(__name__)


class OfficeViewer(PdfViewer):
    def __init__(self, parent):
        super().__init__(parent)
        self._officeView = None
        self._document: Document = None

    @classmethod
    def viewerName(cls):
        return "OfficeViewer"

    @classmethod
    def supportedFormats(cls) -> list[str]:
        return [".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt"]

    @Slot()
    def handleConversionStarted(self):
        self.waitingspinner = WaitingSpinner(self, True, False)
        self.waitingspinner.start()

    @Slot(object)
    def handleConversionEnded(self, r):
        logger.debug(f"converted file={r}")

        if isinstance(r, Exception):
            logger.error(f"Error converting doc: {r}")
            msg = QtWidgets.QMessageBox.critical(self, "Document convertion -- Failed", f"{r}")
        else:
            self._document.filepath = r
            self.loadDocument(self._document.filepath.as_posix())

        self.waitingspinner.stop()

    def initViewer(self):
        super().initViewer()
