import logging
from pathlib import Path
from qtpy import (QtCore, QtWidgets, Signal, Slot)

from documentviewer.pdfviewer import PdfViewer
from db.dbstructure import Document

from widgets.waitingspinner import WaitingSpinner

from utilities.msoffice2pdf import convert

logger = logging.getLogger(__name__)


class ConverterThread(QtCore.QThread):
    sig_conversion_ended = Signal()

    def __init__(self, filepath: Path, parent: QtCore.QObject | None = None):
        super().__init__(parent)
        self._filepath = filepath

    def run(self):
        self.converted_pdf = convert(self._filepath, self._filepath.parent)
        self.sig_conversion_ended.emit()

    def pdf(self):
        return self.converted_pdf


class OfficeViewer(PdfViewer):
    def __init__(self, model, parent):
        super().__init__(model, parent)
        self._officeView = None
        self._document = None

    @classmethod
    def viewerName(cls):
        return "OfficeViewer"

    @classmethod
    def supportedFormats(cls) -> list[str]:
        return [".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt"]

    def document(self):
        return self._document

    @Slot()
    def handleConversionStarted(self):
        self.waitingspinner = WaitingSpinner(self, True, False)
        self.waitingspinner.start()

    @Slot(object)
    def handleConversionEnded(self, r: object):
        self.waitingspinner.stop()

        if isinstance(r, Exception):
            logger.error(f"Error converting doc: {r}")
            QtWidgets.QMessageBox.critical(self, "Document convertion -- Failed", f"{r}")
        else:
            self._document.filepath = str(r)
            self.loadDocument()

    def initViewer(self, doc: Document, model_index: QtCore.QModelIndex):
        self._document = doc
        super().initViewer(doc, model_index)
