import logging
from math import sqrt

import fitz

from db.dbstructure import Document
from documentviewer.viewerwidget import ViewerWidget
from qtpy import (QtCore, QtGui, QtPdf, QtPdfWidgets, QtWidgets, Signal, Slot)

ZOOM_LEVELS = ["Fit Width", "Fit Page", "12%", "25%", "33%", "50%", "66%",
               "75%", "100%", "125%", "150%", "200%", "400%"]

ZOOM_MULTIPLIER = sqrt(2.0)

logger = logging.getLogger(__name__)


class ZoomSelector(QtWidgets.QComboBox):
    zoomModeChanged = Signal(QtPdfWidgets.QPdfView.ZoomMode)
    zoomFactorChanged = Signal(float)

    def __init__(self, parent):
        super().__init__(parent)
        self.setEditable(True)

        for zoom_level in ZOOM_LEVELS:
            self.addItem(zoom_level)

        self.currentTextChanged.connect(self.onCurrentTextChanged)
        self.lineEdit().editingFinished.connect(self._editingFinished)

    @Slot()
    def _editingFinished(self):
        self.onCurrentTextChanged(self.lineEdit().text())

    @Slot(float)
    def setZoomFactor(self, zoomFactor):
        zoom_level = int(100 * zoomFactor)
        self.setCurrentText(f"{zoom_level}%")

    @Slot()
    def reset(self):
        self.setCurrentIndex(8)  # 100%

    @Slot(str)
    def onCurrentTextChanged(self, text: str):
        if text == "Fit Width":
            self.zoomModeChanged.emit(QtPdfWidgets.QPdfView.ZoomMode.FitToWidth)
        elif text == "Fit Page":
            self.zoomModeChanged.emit(QtPdfWidgets.QPdfView.ZoomMode.FitInView)
        else:
            factor = 1.0
            withoutPercent = text.replace('%', '')
            zoomLevel = int(withoutPercent)
            if zoomLevel:
                factor = zoomLevel / 100.0

            self.zoomModeChanged.emit(QtPdfWidgets.QPdfView.ZoomMode.Custom)
            self.zoomFactorChanged.emit(factor)

class PdfViewWithLinks(QtPdfWidgets.QPdfView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.link_model: QtPdf.QPdfLinkModel = None

    def mouseMoveEvent(self, event: QtGui.QMouseEvent | None) -> None:
        return  # issue #22

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent | None) -> None:
        return  # issue #22

    def mousePressEvent(self, event: QtGui.QMouseEvent | None) -> None:      
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            zoom_factor = self.zoomFactor()

            # Get the current page number (0-based index)
            current_page = self.pageNavigator().currentPage()

            # Get the size of the current page (in points)
            page_size = self.document().pagePointSize(current_page)            

            # Get the scroll position of the viewport
            scroll_position = self.horizontalScrollBar().value(), self.verticalScrollBar().value()

            # Calculate the visible top-left corner in PDF coordinates
            top_left_corner = QtCore.QPointF(scroll_position[0] / zoom_factor, scroll_position[1] / zoom_factor)

            # print(f"Zoom Factor: {zoom_factor}")
            # print(f"Page Size: {page_size}")
            # print(f"Scroll Position: {scroll_position}")
            # print(f"Top Left Corner (PDF Coordinates): {top_left_corner}")

    def setLinkModel(self, link_model):
        self.link_model = link_model

    def paintEvent(self, event):
        super().paintEvent(event)

        if not self.link_model:
            return

        painter = QtGui.QPainter(self.viewport())

        pen_color = QtGui.QColor(0, 255, 0, 128)  # Semi-transparent green
        brush_color = QtGui.QColor(0, 255, 0, 50)  # Light green fill
        painter.setPen(pen_color)
        painter.setBrush(brush_color)

        page_number = self.pageNavigator().currentPage()

        # Iterate over all links in the document
        for link_index in range(self.link_model.rowCount(QtCore.QModelIndex())):
            # Get the link details
            idx = self.link_model.index(link_index, 0)
            link: QtPdf.QPdfLink = self.link_model.data(idx, QtPdf.QPdfLinkModel.Role.Link.value)

            if link.page() == page_number:
                link_rect = link.rectangles()

                # Transform the link rectangle to the current page's scale and position
                for rect in link_rect:
                    view_geometry = self.viewport().geometry()

                    # transform = QtGui.QTransform()

                    # Draw the rectangle as a highlight around the link
                    painter.drawRect(rect)

        painter.end()


class PdfViewer(ViewerWidget):
    def __init__(self, model, parent):
        super().__init__(model, parent=parent)
        self.pdfView = None
        self.pdfdocument = None
        self.searchmodel = None
        self.linkmodel = None
        self._document = None
        self._parent = parent

    @classmethod
    def viewerName(cls):
        return "PdfViewer"

    @classmethod
    def supportedFormats(cls) -> list[str]:
        return [".pdf"]

    def document(self):
        return self._document

    def loadDocument(self):
        self.pdfdocument.load(self._document.filepath.as_posix())
        self.pdfView.setDocument(self.pdfdocument)
        self.linkmodel.setDocument(self.pdfdocument)
        self.bookmarkModel.setDocument(self.pdfdocument)
        self.page_count.setText(f" of {self.pdfdocument.pageCount()}")

    def initViewer(self, doc: Document, model_index: QtCore.QModelIndex):
        self._document = doc

        self.pdfView = PdfViewWithLinks(self)
        self.pdfdocument = QtPdf.QPdfDocument(self.pdfView)
        self.linkmodel = QtPdf.QPdfLinkModel(self.pdfView)

        # self.pdfView.setLinkModel(self.linkmodel)  # issue #22

        self.scroll_area.setWidget(self.pdfView)

        self.pdfView.setPageMode(QtPdfWidgets.QPdfView.PageMode.MultiPage)

        # Bookmarks
        self.bookmarkModel = QtPdf.QPdfBookmarkModel(self)
        self.bookmarks = QtWidgets.QTreeView(self.left_pane)
        self.bookmarks.setHeaderHidden(True)
        self.bookmarks.setModel(self.bookmarkModel)
        self.left_pane.addTab(self.bookmarks, "Bookmarks")
        self.bookmarks.activated.connect(self.bookmarkSelected)

        # Searchtab
        self.searchlist = QtWidgets.QTableView(self.left_pane)
        self.searchlist.horizontalHeader().hide()
        self.searchlist.horizontalHeader().setStretchLastSection(True)
        self.left_pane.addTab(self.searchlist, "Search")

        # Linktab
        self.linklist = QtWidgets.QTableView(self.left_pane)
        self.linklist.setModel(self.linkmodel)
        self.searchlist.horizontalHeader().hide()
        self.searchlist.horizontalHeader().setStretchLastSection(True)
        self.linklist.clicked.connect(self.onLinkListClicked)
        linktab_idx = self.left_pane.addTab(self.linklist, "Link")
        
        self.left_pane.setTabVisible(linktab_idx, False)  # remove this code to show the link tab > see issue #22

        # TOOLBAR

        # Search tool

        self.searchfield = QtWidgets.QLineEdit(self._toolbar)
        self.searchfield.setPlaceholderText("Search...")
        self.searchfield.setFixedWidth(180)
        self.action_search = self._toolbar.insertWidget(self.toolbarFreeSpace(), self.searchfield)
        self.searchfield.editingFinished.connect(self.onSearchTriggered)
        
        self.btn_previous_searchresult = QtWidgets.QToolButton(self._toolbar)
        self.btn_previous_searchresult.setIcon(QtGui.QIcon(':arrow-up-s-line'))
        self.btn_previous_searchresult.setEnabled(True)
        self.action_previous_searchresult = self._toolbar.insertWidget(self.toolbarFreeSpace(), self.btn_previous_searchresult)
        self.btn_previous_searchresult.clicked.connect(self.previousSearchResult)

        self.btn_next_searchresult = QtWidgets.QToolButton(self._toolbar)
        self.btn_next_searchresult.setIcon(QtGui.QIcon(':arrow-down-s-line'))
        self.btn_next_searchresult.setEnabled(True)
        self.action_next_searchresult = self._toolbar.insertWidget(self.toolbarFreeSpace(), self.btn_next_searchresult)
        self.btn_next_searchresult.clicked.connect(self.nextSearchResult)

        self.btn_clear_searchresult = QtWidgets.QToolButton(self._toolbar)
        self.btn_clear_searchresult.setIcon(QtGui.QIcon(':close-line'))
        self.btn_clear_searchresult.setToolTip("Clear search result")
        self.btn_clear_searchresult.setEnabled(True)
        self.action_clearsearch = self._toolbar.insertWidget(self.toolbarFreeSpace(), self.btn_clear_searchresult)
        self.btn_clear_searchresult.clicked.connect(self.onClearSearch)

        self._toolbar.insertSeparator(self.toolbarFreeSpace())

        # zoom selector
        self._zoomselector = ZoomSelector(self._toolbar)

        self.btn_fitwidth = QtWidgets.QToolButton(self._toolbar)
        self.btn_fitwidth.setIcon(QtGui.QIcon(':expand-width-fill'))
        self.btn_fitwidth.clicked.connect(self.fitwidth)

        self.btn_fitheight = QtWidgets.QToolButton(self._toolbar)
        self.btn_fitheight.setIcon(QtGui.QIcon(':expand-height-line'))
        self.btn_fitheight.clicked.connect(self.fitheight)

        self._toolbar.insertWidget(self.toolbarFreeSpace(), self._zoomselector)
        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.btn_fitwidth)
        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.btn_fitheight)
        self._toolbar.insertSeparator(self.toolbarFreeSpace())

        # Navigator
        navigator = self.pdfView.pageNavigator()
        self.pageSelector = QtPdfWidgets.QPdfPageSelector(self._toolbar)
        self.pageSelector.setDocument(self.pdfdocument)
        self.pageSelector.currentPageChanged.connect(self.pageSelected)
        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.pageSelector)
        self.page_count = QtWidgets.QLabel(self._toolbar)
        self.page_count.setText(f" of {self.pdfdocument.pageCount()}")
        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.page_count)
        self._toolbar.insertSeparator(self.toolbarFreeSpace())

        navigator.currentPageChanged.connect(self.pageSelector.setCurrentPage)

        self.previous_page_btn = QtWidgets.QToolButton(self._toolbar)
        self.previous_page_btn.setIcon(QtGui.QIcon(':arrow-up-s-line'))
        self.previous_page_btn.setEnabled(False)

        self.next_page_btn = QtWidgets.QToolButton(self._toolbar)
        self.next_page_btn.setIcon(QtGui.QIcon(':arrow-down-s-line'))
        self.next_page_btn.setEnabled(False)

        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.previous_page_btn)
        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.next_page_btn)
        self._toolbar.insertSeparator(self.toolbarFreeSpace())

        navigator.backAvailableChanged.connect(self.previous_page_btn.setEnabled)
        navigator.forwardAvailableChanged.connect(self.next_page_btn.setEnabled)
        self.previous_page_btn.clicked.connect(self.onActionBackTriggered)
        self.next_page_btn.clicked.connect(self.onActionForwardTriggered)

        # Zoom
        self.action_zoom_in = QtWidgets.QToolButton(self)
        self.action_zoom_in.setIcon(QtGui.QIcon(":zoom-in"))
        self.action_zoom_in.clicked.connect(self.onActionZoomInTriggered)
        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.action_zoom_in)

        self.action_zoom_out = QtWidgets.QToolButton(self)
        self.action_zoom_out.setIcon(QtGui.QIcon(":zoom-out"))
        self.action_zoom_out.clicked.connect(self.onActionZoomOutTriggered)
        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.action_zoom_out)

        self._zoomselector.zoomModeChanged.connect(self.pdfView.setZoomMode)
        self._zoomselector.zoomFactorChanged.connect(self.pdfView.setZoomFactor)
        self._zoomselector.reset()

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
        self.action_snip.clicked.connect(lambda: self.capture(self.citation()))
        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.action_snip)

        # Rotate
        self.action_rotate = QtWidgets.QToolButton(self)
        self.action_rotate.setIcon(QtGui.QIcon(":anticlockwise"))
        self.action_rotate.setToolTip("Rotate anticlockwise")
        self.action_rotate.clicked.connect(lambda: self.rotate(-90))
        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.action_rotate)

        self.action_rotate = QtWidgets.QToolButton(self)
        self.action_rotate.setIcon(QtGui.QIcon(":clockwise"))
        self.action_rotate.setToolTip("Rotate clockwise")
        self.action_rotate.clicked.connect(lambda: self.rotate(90))
        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.action_rotate)

        self.createMapper(model_index)

    def widget(self):
        return self.pdfView

    @Slot()
    def citation(self) -> str:
        refkey = "refkey: " + self.refKey.text() if self.refKey.text() != "" else None
        page = f"p. {self.pageSelector.currentPageLabel()}"
        title = f'"{self.title.toPlainText()}"'
        citation = "; ".join(x for x in [refkey, title, self.subtitle.text(), self.reference.text(), page] if x)
        return f"[{citation}]"

    @Slot(QtCore.QModelIndex)
    def bookmarkSelected(self, index: QtCore.QModelIndex):
        if not index.isValid():
            return

        page = index.data(int(QtPdf.QPdfBookmarkModel.Role.Page))
        location = index.data(int(QtPdf.QPdfBookmarkModel.Role.Location))
        self.pageSelected(page, location)

    @Slot(int)
    def pageSelected(self, page, location=QtCore.QPointF()):
        nav = self.pdfView.pageNavigator()
        nav.jump(page, location, nav.currentZoom())

    @Slot()
    def onActionZoomInTriggered(self):
        pno = self.pdfView.pageNavigator().currentPage()
        self.pdfView.setZoomFactor(self.pdfView.zoomFactor() * ZOOM_MULTIPLIER)
        self.pageSelected(pno)

    @Slot()
    def onActionZoomOutTriggered(self):
        pno = self.pdfView.pageNavigator().currentPage()
        self.pdfView.setZoomFactor(self.pdfView.zoomFactor() / ZOOM_MULTIPLIER)
        self.pageSelected(pno)

    @Slot()
    def onActionPreviousPageTriggered(self):
        nav = self.pdfView.pageNavigator()
        nav.jump(nav.currentPage() - 1, QtCore.QPointF(), nav.currentZoom())

    @Slot()
    def onActionNextPageTriggered(self):
        nav = self.pdfView.pageNavigator()
        nav.jump(nav.currentPage() + 1, QtCore.QPointF(), nav.currentZoom())

    @Slot()
    def onActionBackTriggered(self):
        self.pdfView.pageNavigator().back()

    @Slot()
    def onActionForwardTriggered(self):
        self.pdfView.pageNavigator().forward()

    @Slot()
    def rotate(self, degree):
        pno = self.pdfView.pageNavigator().currentPage()

        try:
            pdf = fitz.open(self._document.filepath.as_posix())
            page = pdf[pno]
        except Exception as e:
            logger.error(e)
            return
        else:
            rotation = page.rotation + degree
            page.set_rotation(rotation)
            try:
                pdf.saveIncr()
            except Exception as e:
                logger.error(e)
                return
            else:
                self.pdfdocument.load(self._document.filepath.as_posix())
                self.pageSelected(pno)

    @Slot(QtCore.QModelIndex)
    def onSearchListClicked(self, current_idx: QtCore.QModelIndex):
        pno = self.searchmodel.data(current_idx, QtPdf.QPdfSearchModel.Role.Page)
        location = self.searchmodel.data(current_idx, QtPdf.QPdfSearchModel.Role.Location)
        self.pdfView.pageNavigator().jump(pno, location, self.pdfView.pageNavigator().currentZoom())
        self.pdfView.setCurrentSearchResultIndex(current_idx.row())

    @Slot()
    def onClearSearch(self):
        self.searchfield.setText("")
        self.onSearchTriggered()

    @Slot(QtCore.QModelIndex)
    def onLinkListClicked(self, current_idx: QtCore.QModelIndex):
        pno = self.linkmodel.data(current_idx, QtPdf.QPdfLinkModel.Role.Page.value)
        location = self.linkmodel.data(current_idx, QtPdf.QPdfLinkModel.Role.Location.value)
        link: QtPdf.QPdfLink = self.linkmodel.data(current_idx, QtPdf.QPdfLinkModel.Role.Link.value)
        self.pdfView.pageNavigator().jump(link)

        rects = link.rectangles()

        first_rect: QtCore.QRectF = rects[0]
        last_rect: QtCore.QRectF = rects[-1]

        tl = first_rect.topLeft()
        br = last_rect.bottomRight()

        print(f"link: {link.url()}")
        print(f"link: {location}")
        text = self.pdfdocument.getSelection(link.page(), tl, br).text()
        print(f"text: {text}")

    @Slot()
    def onSearchTriggered(self):
        if self.searchmodel is None:
            self.searchmodel = QtPdf.QPdfSearchModel(self.pdfView)
            self.searchmodel.setDocument(self.pdfdocument)
            self.pdfView.setSearchModel(self.searchmodel)
            self.searchlist.setModel(self.searchmodel)
            search_delegate = SearchResultDelegate(self.searchmodel, self.pdfdocument)
            self.searchlist.setItemDelegateForColumn(0, search_delegate)
            self.searchlist.clicked.connect(self.onSearchListClicked)

        self.searchmodel.setSearchString(self.searchfield.text())
        self.search_result_index = -1
        self.pdfView.setCurrentSearchResultIndex(self.search_result_index)

    @Slot()
    def fitwidth(self):
        self._zoomselector.setCurrentText("Fit Width")

    @Slot()
    def fitheight(self):
        self._zoomselector.setCurrentText("Fit Page")

    @Slot()
    def previousSearchResult(self):
        if self.search_result_index > 0:
            self.search_result_index -= 1
            current_idx = self.searchmodel.index(self.search_result_index, 0, QtCore.QModelIndex())
            pno = self.searchmodel.data(current_idx, QtPdf.QPdfSearchModel.Role.Page)
            location = self.searchmodel.data(current_idx, QtPdf.QPdfSearchModel.Role.Location)
            self.pdfView.setCurrentSearchResultIndex(self.search_result_index)
            self.pdfView.pageNavigator().jump(pno, location, self.pdfView.pageNavigator().currentZoom())

    @Slot()
    def nextSearchResult(self):
        if self.search_result_index < self.searchmodel.rowCount(QtCore.QModelIndex())-1:
            self.search_result_index += 1
            current_idx = self.searchmodel.index(self.search_result_index, 0, QtCore.QModelIndex())
            pno = self.searchmodel.data(current_idx, QtPdf.QPdfSearchModel.Role.Page)
            location = self.searchmodel.data(current_idx, QtPdf.QPdfSearchModel.Role.Location)
            self.pdfView.setCurrentSearchResultIndex(self.search_result_index)
            self.pdfView.pageNavigator().jump(pno, location, self.pdfView.pageNavigator().currentZoom())


class SearchResultDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, model, pdfdocument, parent=None):
        super().__init__(parent)
        self.model: QtPdf.QPdfSearchModel = model
        self.pdfdocument: QtPdf.QPdfDocument = pdfdocument

    def initStyleOption(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        super().initStyleOption(option, index)
        pno = self.model.data(index, QtPdf.QPdfSearchModel.Role.Page)
        b_context = self.model.data(index, QtPdf.QPdfSearchModel.Role.ContextBefore)
        a_context = self.model.data(index, QtPdf.QPdfSearchModel.Role.ContextAfter)

        option.features |= QtWidgets.QStyleOptionViewItem.ViewItemFeature.None_
        option.icon = QtGui.QIcon()
        option.text = f"page {self.pdfdocument.pageLabel(pno)}: {b_context[-15:]} {self.model.searchString()} {a_context[:15]}"
