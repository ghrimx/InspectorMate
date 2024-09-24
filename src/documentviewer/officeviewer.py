import logging
from pathlib import Path
from qtpy import (QtCore, Signal)

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

    def loadDocument(self):
        self.waitingspinner = WaitingSpinner(self, True, False)
        self.waitingspinner.start()
        self.converter = ConverterThread(self._document.filepath)
        self.converter.sig_conversion_ended.connect(self.handleConverterResult)
        self.converter.start()

    def handleConverterResult(self):
        self.converter.quit()
        self.waitingspinner.stop()

        converted_pdf = self.converter.pdf()

        if not isinstance(converted_pdf, Exception):
            self.pdfdocument.load(str(converted_pdf))
            self.pdfView.setDocument(self.pdfdocument)
            self.page_count.setText(f" of {self.pdfdocument.pageCount()}")
        else:
            logger.error(f"Error converting doc: {converted_pdf}")

    def initViewer(self, doc: Document, model_index: QtCore.QModelIndex):
        self._document = doc

        super().initViewer(doc, model_index)
