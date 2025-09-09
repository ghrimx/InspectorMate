import logging
from pathlib import Path

from qtpy import QtCore, Signal, Slot

from PyMuPDF4QT.pymupdfviewer import PdfViewer
from documentviewer.imageviewer import ImageViewer
from documentviewer.officeviewer import OfficeViewer
from documentviewer.txtviewer import TxtViewer
from documentviewer.wordviewer import WordViewer

from evidence.evidencemodel import EvidenceModel

from database.dbstructure import Document

import utilities.msoffice2pdf as ms

logger = logging.getLogger(__name__)


class ConverterWorkerSignals(QtCore.QObject):
    started = Signal()
    finished = Signal(object)
    error = Signal(object)
    result = Signal(object)
    progress = Signal(int)


class DocConverterWorker(QtCore.QRunnable):
    def __init__(self, filepath: Path, converter: ms.office2pdf):
        super().__init__()
        self.converter = converter
        self._filepath = filepath
        self.signals = ConverterWorkerSignals()
    
    @Slot()
    def run(self):
        try:
            self.signals.started.emit()
            self.converted_pdf: Path = self.converter(self._filepath, self._filepath.parent)
        except Exception as e:
            self.signals.error.emit(e)
        finally:
            if self.converted_pdf is not None:
                self.signals.finished.emit(self.converted_pdf)
            else:
                e = Exception("File cannot be converted")
                self.signals.error.emit(e)


class ViewerFactory:
    def __init__(self, model: EvidenceModel, mainwindow) -> None:
        self._mainWindow = mainwindow
        self._viewers = {}
        self.threadpool = QtCore.QThreadPool()
        self._model = model

        # Register the classes
        classViewer: PdfViewer | ImageViewer | WordViewer| OfficeViewer | TxtViewer
        for classViewer in [PdfViewer, ImageViewer, WordViewer, OfficeViewer, TxtViewer]:
            self._viewers[classViewer.viewerName()] = classViewer
    
    def viewer(self, doc: Document, index: QtCore.QModelIndex):

        if not doc.exists():
            return None
            
        viewer: PdfViewer | ImageViewer | WordViewer | OfficeViewer | TxtViewer = self.viewerFromExtension(doc.extension())

        if not viewer:
            return None
        
        if isinstance(viewer, OfficeViewer):
            self.convert(doc, viewer)
        
        err = viewer.initViewer()

        if isinstance(err, Exception):
            return None
        
        viewer.createMapper(self._model, index)
        viewer.document = doc
        viewer.loadDocument(doc.filepath.as_posix())

        return viewer

    def viewerFromExtension(self, extension: str):
        viewer: PdfViewer | ImageViewer | WordViewer | OfficeViewer | TxtViewer
        for viewer in self._viewers.values():
            if extension in viewer.supportedFormats():
                return viewer(self._mainWindow)
            
    def convert(self, doc: Document, viewer: OfficeViewer):
        """Convert Office document to PDF"""
        worker = DocConverterWorker(doc.filepath, ms.convert2pdf)
        worker.signals.started.connect(viewer.handleConversionStarted)
        worker.signals.finished.connect(viewer.handleConversionEnded)
        worker.signals.error.connect(viewer.handleConversionEnded)
        self.threadpool.tryStart(worker)

    