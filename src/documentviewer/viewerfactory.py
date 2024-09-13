import logging
from qtpy import QtCore

from documentviewer.pdfviewer import PdfViewer
from documentviewer.imageviewer import ImageViewer
from documentviewer.officeviewer import OfficeViewer
from documentviewer.txtviewer import TxtViewer

from db.dbstructure import Document

logger = logging.getLogger(__name__)

class ViewerFactory:
    def __init__(self, model, mainwindow) -> None:
        self._model = model
        self._mainWindow = mainwindow
        self._viewers = {}

        # Register the classes
        classViewer: PdfViewer | ImageViewer | OfficeViewer | TxtViewer
        for classViewer in [PdfViewer, ImageViewer, OfficeViewer, TxtViewer]:
            self._viewers[classViewer.viewerName()] = classViewer
    
    def viewer(self, doc: Document, index: QtCore.QModelIndex):

        if not doc.exists():
            return None
            
        viewer: PdfViewer | ImageViewer | OfficeViewer | TxtViewer = self.viewerFromExtension(doc.extension())

        if not viewer:
            return None
        
        err = viewer.initViewer(doc, index)

        if isinstance(err, Exception):
            return None
        
        viewer.loadDocument()

        return viewer

    def viewerFromExtension(self, extension: str):
        viewer: PdfViewer | ImageViewer | OfficeViewer | TxtViewer
        for viewer in self._viewers.values():
            if extension in viewer.supportedFormats():
                return viewer(self._model, self._mainWindow)