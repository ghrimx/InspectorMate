from qtpy import (QtCore, QtWidgets, QtGui, Slot)

from documentviewer.viewerwidget import ViewerWidget

from db.dbstructure import Document


class ImageViewer(ViewerWidget):
    def __init__(self, model, parent):
        super().__init__(model, parent=parent)
        self._imageView = None
        self._document = None
        self._image = None
        self._scaleFactor = 0.0

    @classmethod
    def viewerName(cls):
        return "ImageViewer"

    @classmethod
    def supportedFormats(cls) -> list[str]:
        return [".png", ".jpeg", ".jpg"]

    def document(self):
        return self._document

    def loadDocument(self):
        self._image.load(self._document.filepath.as_posix())
        self._imageView.setPixmap(QtGui.QPixmap.fromImage(self._image))
        self.normalSize()

    def initViewer(self, doc: Document, model_index: QtCore.QModelIndex):
        self._document = doc

        self.left_pane.hide()
        self._toolbar.removeAction(self.action_fold_left_sidebar)
        self._toolbar.removeAction(self.action_first_separator)

        self._imageView = QtWidgets.QLabel(self)
        self._imageView.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Ignored)
        self._imageView.setBackgroundRole(QtGui.QPalette.ColorRole.Light)
        self._imageView.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self._image = QtGui.QImage()

        self.scroll_area.setBackgroundRole(QtGui.QPalette.ColorRole.Light)
        self.scroll_area.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self._imageView)

        self._imageView.setScaledContents(True)
        self.scroll_area.setWidgetResizable(False)

        # Zoom
        self.action_zoom_in = QtWidgets.QToolButton(self._toolbar)
        self.action_zoom_in.setIcon(QtGui.QIcon(":zoom-in"))
        self.action_zoom_in.clicked.connect(self.onActionZoomInTriggered)
        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.action_zoom_in)

        self.action_zoom_out = QtWidgets.QToolButton(self._toolbar)
        self.action_zoom_out.setIcon(QtGui.QIcon(":zoom-out"))
        self.action_zoom_out.clicked.connect(self.onActionZoomOutTriggered)
        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.action_zoom_out)

        self.action_reset_aspect_ratio = QtWidgets.QToolButton(self._toolbar)
        self.action_reset_aspect_ratio.setIcon(QtGui.QIcon(":aspect-ratio-line"))
        self.action_reset_aspect_ratio.clicked.connect(self.normalSize)
        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.action_reset_aspect_ratio)

        self.action_fit_window = QtWidgets.QToolButton(self._toolbar)
        self.action_fit_window.setIcon(QtGui.QIcon(":expand-diagonal-line"))
        self.action_fit_window.setCheckable(True)
        self.action_fit_window.clicked.connect(self.fitToWindow)
        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.action_fit_window)

        # Citation
        self.action_cite = QtWidgets.QToolButton(self)
        self.action_cite.setIcon(QtGui.QIcon(":double-quotes"))
        self.action_cite.setShortcut(QtGui.QKeySequence("Ctrl+Alt+C"))
        self.action_cite.setToolTip("Copy citation (Ctrl+Alt+C)")
        self.action_cite.clicked.connect(lambda: self.cite(self.citation()))
        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.action_cite)

        # Snipping tool
        self.action_snip = QtWidgets.QToolButton(self)
        self.action_snip.setIcon(QtGui.QIcon(":capture_area"))
        self.action_snip.setShortcut(QtGui.QKeySequence("Ctrl+Alt+S"))
        self.action_snip.setToolTip("Capture Area (Ctrl+Alt+S)")
        self.action_snip.clicked.connect(self.capture)
        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.action_snip)

        self.normalSize()

        self.createMapper(model_index)

    def widget(self):
        return self._imageView

    def adjustScrollBar(self, scrollBar: QtWidgets.QScrollBar, factor: float):
        scrollBar.setValue(int(factor * scrollBar.value() + ((factor - 1) * scrollBar.pageStep() / 2)))

    def scaleImage(self, factor: float):
        self._scaleFactor *= factor
        self._imageView.resize(self._scaleFactor * self._imageView.pixmap().size())

        self.adjustScrollBar(self.scroll_area.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scroll_area.verticalScrollBar(), factor)

        self.updateActions()

    def updateActions(self):
        self.action_zoom_in.setEnabled(self._scaleFactor < 3.0 and not self.action_fit_window.isChecked())
        self.action_zoom_out.setEnabled(self._scaleFactor > 0.333 and not self.action_fit_window.isChecked())
        self.action_reset_aspect_ratio.setEnabled(not self.action_fit_window.isChecked())

    Slot()
    def citation(self) -> str:
        refkey = "refkey: " + self.refKey.text() if self.refKey.text() != "" else None
        title = f'"{self.title.toPlainText()}"'
        citation = "; ".join(x for x in [refkey, title, self.subtitle.text(), self.reference.text()] if x)
        return f"[{citation}]"

    Slot()
    def onActionZoomInTriggered(self):
        self.scaleImage(1.25)

    Slot()
    def onActionZoomOutTriggered(self):
        self.scaleImage(0.8)

    Slot()
    def normalSize(self):
        self._imageView.adjustSize()
        self._scaleFactor = 1.0
        self.updateActions()

    @Slot()
    def fitToWindow(self):
        fitToWindow = self.action_fit_window.isChecked()
        self.scroll_area.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()

        self.updateActions()
